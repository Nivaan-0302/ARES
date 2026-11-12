
from flask import Flask, jsonify, request, send_from_directory, abort, g
import rasterio
import numpy as np
from terrain_region import analyze_region
from pathlib import Path
import math
import os
from threading import BoundedSemaphore
from dem_data import (DEM_PATH, validate_dem, validate_global_coverage,
                      sample_point, slope_at_point, DEMValidationError)
from route_planner import (
    astar_route,
    grid_route_to_coordinates,
    coordinates_to_grid,
    calculate_route_distance,

)
BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=None)
# Only these reviewed frontend files are public. Never expose the project root,
# data directory, Python sources, dotfiles, or future configuration files.
PUBLIC_ASSETS = frozenset({
    "index.html", "mars_hero.png", "style.css", "ares_3d.css",
    "mission_control.css", "cosmic.css", "orbital_workspace.css",
    "public_polish.css", "mission_brief.css", "supreme_navigation.css",
    "mission_state.js", "mission_service.js", "mission_geometry.js",
    "globe_bootstrap.js", "mission_control.js", "phase4_intelligence.js",
    "phase5_comparison.js", "script.js", "globe.js", "cosmic.js",
    "orbital_workspace.js", "public_polish.js", "mission_brief.js",
    "supreme_navigation.js",
})
_point_paths = {"/api/elevation", "/api/slope", "/api/terrain-region"}
_route_paths = {
    "/api/route", "/api/mission-route", "/api/global-route",
    "/api/refined-route", "/api/route-comparison",
}
_expensive_paths = _route_paths | {"/api/terrain-region", "/api/global-relief"}
_slot_count = int(os.environ.get("ARES_MAX_CONCURRENT_ANALYSES", "4"))
if not 1 <= _slot_count <= 64:
    raise RuntimeError("ARES_MAX_CONCURRENT_ANALYSES must be between 1 and 64")
_analysis_slots = BoundedSemaphore(_slot_count)


@app.before_request
def validate_and_bound_api_work():
    """Reject malformed coordinates before DEM I/O and bound concurrent work."""
    keys = ("lat", "lon") if request.path in _point_paths else (
        ("start_lat", "start_lon", "end_lat", "end_lon")
        if request.path in _route_paths else ()
    )
    if keys:
        try:
            values = [float(request.args[key]) for key in keys]
        except (KeyError, ValueError, TypeError):
            return jsonify(status="invalid_coordinates", error="Provide valid " + ", ".join(keys)), 400
        if any(not math.isfinite(v) or abs(v) > (90 if i % 2 == 0 else 180)
               for i, v in enumerate(values)):
            return jsonify(status="invalid_coordinates", error="Coordinates must be finite; latitude -90 to 90 and longitude -180 to 180."), 400
    if request.path in _expensive_paths:
        if not _analysis_slots.acquire(blocking=False):
            response = jsonify(status="busy", error="Terrain analysis is busy. Please retry shortly.")
            response.status_code = 503
            response.headers["Retry-After"] = "1"
            return response
        g.ares_analysis_slot = True


@app.teardown_request
def release_analysis_slot(_error):
    if g.pop("ares_analysis_slot", False):
        _analysis_slots.release()


@app.after_request
def response_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    if request.path.startswith("/api/") or request.path == "/readyz":
        response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/<path:asset_path>")
def public_asset(asset_path):
    if asset_path in PUBLIC_ASSETS:
        return send_from_directory(BASE_DIR, asset_path)
    if asset_path.startswith("vendor/"):
        return send_from_directory(BASE_DIR / "vendor", asset_path[len("vendor/"):])
    abort(404)


@app.get("/healthz")
def health():
    return jsonify(status="ok")


@app.get("/readyz")
def readiness():
    try:
        with rasterio.open(DEM_PATH) as dem:
            metadata = validate_dem(dem)
            try:
                validate_global_coverage(metadata)
            except DEMValidationError:
                return jsonify(status="not_ready",dataset=metadata,
                    capabilities={"regional":True,"global":False},
                    error="Dataset supports regional analysis; global planning requires full-planet coverage."),503
        return jsonify(status="ready", dataset=metadata)
    except Exception:
        app.logger.exception("Terrain dataset readiness check failed")
        return jsonify(status="not_ready", error="MOLA raster is missing or incompatible. Check ARES_DEM_PATH and dataset metadata in the server logs."), 503


@app.route("/api/elevation")
def get_elevation():
    try:
        latitude = float(request.args["lat"])
        longitude = float(request.args["lon"])

        if not (-90 <= latitude <= 90):
            return jsonify({"error": "Invalid latitude"}), 400

        if not (-180 <= longitude <= 180):
            return jsonify({"error": "Invalid longitude"}), 400

        with rasterio.open(DEM_PATH) as dem:
            metadata=validate_dem(dem)
            elevation = sample_point(dem, latitude, longitude)
            if elevation is None:
                return jsonify(status="no_data", error="No elevation data at this coordinate"), 404

        return jsonify({
            "latitude": latitude,
            "longitude": longitude,
            "elevation_m": elevation,
            "elevation_units_assumed":metadata['elevation_units_assumed'],
            "source": "Configured MOLA-derived DEM",
            "input_provenance": "Local derivative; source product and processing history not yet independently identified"
        })

    except (KeyError, ValueError):
        return jsonify({"error": "Provide valid lat and lon"}), 400

    except DEMValidationError as exc:
        return jsonify(status="dataset_unavailable", error=str(exc)), 503
    except rasterio.errors.RasterioIOError:
        app.logger.exception("Configured terrain dataset could not be opened")
        return jsonify(status="dataset_unavailable", error="Configured terrain data is unavailable. Check the dataset configuration."), 503
    except Exception:
        app.logger.exception("Elevation lookup failed")
        return jsonify({"error": "Elevation lookup failed"}), 500


# ARES — NASA MOLA Terrain Slope API

MARS_RADIUS_METRES = 3389500


@app.route("/api/slope")
def get_slope():
    try:
        latitude = float(request.args["lat"])
        longitude = float(request.args["lon"])

        if not np.isfinite(latitude) or not np.isfinite(longitude):
            return jsonify({"error": "Coordinates must be finite"}), 400

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return jsonify({"error": "Invalid coordinates"}), 400

        with rasterio.open(DEM_PATH) as dem:
            metadata=validate_dem(dem)
            elevation = sample_point(dem, latitude, longitude)
            slope_degrees = slope_at_point(dem, latitude, longitude)
            if elevation is None or slope_degrees is None:
                return jsonify(status="no_data", error="Slope unavailable at this dataset boundary or missing-data neighborhood"), 404

            # ARES — DEM-scale terrain steepness classification
            if slope_degrees <= 5:
                hazard_level = "LOW"
            elif slope_degrees <= 15:
                hazard_level = "MODERATE"
            elif slope_degrees <= 25:
                hazard_level = "HIGH"
            else:
                hazard_level = "EXTREME"
    
            

            return jsonify({
                "latitude": latitude,
                "longitude": longitude,
                "elevation_m": float(elevation),
                "slope_degrees": round(slope_degrees, 3),
                "distance_model":"Mean-radius sphere with latitude-dependent spacing",
                "elevation_units_assumed":metadata['elevation_units_assumed'],
                "hazard_level": hazard_level,
                "method": "Central axial differences at native pixel centres; valid centre and four axial neighbours",
                "source": "Configured MOLA-derived DEM",
            "input_provenance": "Local derivative; source product and processing history not yet independently identified",
                "warning": "DEM-scale slope; not a rover-scale obstacle assessment"
            })

    except (KeyError, ValueError):
        return jsonify({
            "error": "Provide valid lat and lon"
        }), 400

    except DEMValidationError as exc:
        return jsonify(status="dataset_unavailable", error=str(exc)), 503
    except rasterio.errors.RasterioIOError:
        app.logger.exception("Configured terrain dataset could not be opened")
        return jsonify(status="dataset_unavailable", error="Configured terrain data is unavailable. Check the dataset configuration."), 503
    except Exception:
        app.logger.exception("Slope calculation failed")
        return jsonify({
            "error": "Slope calculation failed"
        }), 500


# ARES — Regional Terrain Hazard API

@app.route("/api/terrain-region")
def get_terrain_region():
    try:
        latitude = float(request.args["lat"])
        longitude = float(request.args["lon"])

        if not np.isfinite(latitude) or not np.isfinite(longitude):
            return jsonify({"error": "Invalid coordinates"}), 400

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return jsonify(status="invalid_coordinates", error="Invalid Mars coordinates"), 400

        result = analyze_region(
            latitude=latitude,
            longitude=longitude,
            radius_degrees=0.25
        )

        return jsonify(result)

    except KeyError:
        return jsonify(status="invalid_coordinates", error="Provide valid lat and lon"), 400
    except ValueError as exc:
        return jsonify(status="outside_coverage", error=str(exc)), 422

    except DEMValidationError as exc:
        return jsonify(status="dataset_unavailable", error=str(exc)), 503
    except rasterio.errors.RasterioIOError:
        app.logger.exception("Configured terrain dataset could not be opened")
        return jsonify(status="dataset_unavailable", error="Configured terrain data is unavailable. Check the dataset configuration."), 503
    except Exception:
        app.logger.exception("Regional terrain analysis failed")
        return jsonify({"error": "Regional analysis failed"}), 500



@app.route("/api/route")
def calculate_autonomous_route():
    try:
        required = ("start_lat", "start_lon", "end_lat", "end_lon")

        if any(request.args.get(key) is None for key in required):
            return jsonify({
                "error": "Provide start_lat, start_lon, end_lat and end_lon"
            }), 400

        start_lat = float(request.args["start_lat"])
        start_lon = float(request.args["start_lon"])
        end_lat = float(request.args["end_lat"])
        end_lon = float(request.args["end_lon"])

        import math

        values = (start_lat, start_lon, end_lat, end_lon)

        if not all(math.isfinite(value) for value in values):
            return jsonify({"error": "Coordinates must be finite"}), 400

        if not (
            -90 <= start_lat <= 90
            and -90 <= end_lat <= 90
            and -180 <= start_lon <= 180
            and -180 <= end_lon <= 180
        ):
            return jsonify({"error": "Invalid Mars coordinates"}), 400

        # Analyze the terrain around the landing site
        terrain = analyze_region(start_lat, start_lon)

        hazard_grid = terrain["hazard_grid"]
        bounds = terrain["bounds"]

        rows = len(hazard_grid)
        cols = len(hazard_grid[0])
        shape = (rows, cols)

        start = coordinates_to_grid(
            start_lat, start_lon, bounds, shape
        )

        goal = coordinates_to_grid(
            end_lat, end_lon, bounds, shape
        )

        # Never pretend to route beyond the analyzed terrain
        if start is None or goal is None:
            return jsonify({
                "status": "outside_region",
                "message": (
                    "Both locations must be inside the "
                    "analyzed MOLA terrain region."
                ),
                "bounds": bounds
            }), 422

        
        route = astar_route(hazard_grid, start, goal, bounds=bounds)


        if route is None:
            return jsonify({
                "status": "no_route",
                "message": "No traversable route found."
            }), 422

        centres = grid_route_to_coordinates(route, bounds, shape)
        coordinates = ([[start_lat, start_lon], [end_lat, end_lon]] if start == goal
                       else [[start_lat, start_lon]] + centres + [[end_lat, end_lon]])

        hazard_counts = {
            "low": 0,
            "moderate": 0,
            "high": 0,
            "extreme": 0
        }

        hazard_names = {
            0: "low",
            1: "moderate",
            2: "high",
            3: "extreme"
        }

        for row, col in route:
            hazard_level = int(hazard_grid[row][col])
            hazard_name = hazard_names.get(hazard_level)

            if hazard_name is not None:
                hazard_counts[hazard_name] += 1

        
        risk_weights = {
            "low": 0,
            "moderate": 1,
            "high": 3,
            "extreme": 6
        }

        total_risk = sum(
            hazard_counts[level] * weight
            for level, weight in risk_weights.items()
        )

        maximum_risk = len(route) * 6

        terrain_risk_score = round(
            (total_risk / maximum_risk) * 100,
            2
        ) if maximum_risk > 0 else 0.0



        from mission_routing import route_metrics
        metrics = route_metrics(coordinates, [start_lat, start_lon], [end_lat, end_lon])

        return jsonify({
            "status": "success",
            "algorithm": "A*",
            "data_source": "NASA MOLA",
            "route_type": "regional_dem_scale",
            "start_cell": list(start),
            "goal_cell": list(goal),
            **metrics,
            "hazard_breakdown": hazard_counts,
            "terrain_risk_score": terrain_risk_score,
            "route_coordinates": coordinates,
            "bounds": bounds
        })

    except (ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400

    except DEMValidationError as exc:
        return jsonify(status="dataset_unavailable", error=str(exc)), 503
    except rasterio.errors.RasterioIOError:
        app.logger.exception("Configured terrain dataset could not be opened")
        return jsonify(status="dataset_unavailable", error="Configured terrain data is unavailable. Check the dataset configuration."), 503
    except Exception:
        app.logger.exception("ARES route-planning error")
        return jsonify({
            "error": "Route calculation failed"
        }), 500


# ARES 3.0 — Coarse planet-wide routing and globe relief


@app.route("/api/mission-route")
def mission_route():
    """The single API used by map clicks and typed coordinates in both views."""
    try:
        from mission_routing import calculate_mission_route
        keys = ("start_lat", "start_lon", "end_lat", "end_lon")
        coords = [float(request.args[key]) for key in keys]
        result = calculate_mission_route(*coords)
        return jsonify(result), (200 if result.get("status") == "success" else 422)
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"status": "invalid_coordinates", "error": str(exc)}), 400
    except DEMValidationError as exc:
        return jsonify(status="dataset_unavailable", error=str(exc)), 503
    except rasterio.errors.RasterioIOError:
        app.logger.exception("Configured terrain dataset could not be opened")
        return jsonify(status="dataset_unavailable", error="Configured terrain data is unavailable. Check the dataset configuration."), 503
    except Exception:
        app.logger.exception("Mission route calculation failed")
        return jsonify({"status": "error", "error": "Mission routing failed; check server logs."}), 500

@app.route("/api/global-route")
def global_route():
    try:
        from global_navigation import plan
        keys = ("start_lat", "start_lon", "end_lat", "end_lon")
        coords = [float(request.args[key]) for key in keys]
        result = plan(*coords)
        return jsonify(result), (200 if result["status"] == "success" else 422)
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except DEMValidationError as exc:
        return jsonify(status="dataset_unavailable", error=str(exc)), 503
    except rasterio.errors.RasterioIOError:
        app.logger.exception("Configured terrain dataset could not be opened")
        return jsonify(status="dataset_unavailable", error="Configured terrain data is unavailable. Check the dataset configuration."), 503
    except Exception:
        app.logger.exception("Global routing failed")
        return jsonify({"error":"Global routing failed"}), 500


@app.route("/api/refined-route")
def refined_route():
    try:
        from route_refinement import refine_global_route
        keys = ("start_lat", "start_lon", "end_lat", "end_lon")
        coords = [float(request.args[key]) for key in keys]
        result = refine_global_route(*coords)
        return jsonify(result), (200 if result["status"] == "success" else 422)
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except DEMValidationError as exc:
        return jsonify(status="dataset_unavailable", error=str(exc)), 503
    except rasterio.errors.RasterioIOError:
        app.logger.exception("Configured terrain dataset could not be opened")
        return jsonify(status="dataset_unavailable", error="Configured terrain data is unavailable. Check the dataset configuration."), 503
    except Exception:
        app.logger.exception("Sampled global refinement failed")
        return jsonify({"error":"Sampled refinement failed"}), 500


@app.route("/api/global-relief")
def global_relief():
    try:
        from global_navigation import relief
        return jsonify(relief())
    except DEMValidationError as exc:
        return jsonify(status="dataset_unavailable", error=str(exc)), 503
    except rasterio.errors.RasterioIOError:
        app.logger.exception("Configured terrain dataset could not be opened")
        return jsonify(status="dataset_unavailable", error="Configured terrain data is unavailable. Check the dataset configuration."), 503
    except Exception:
        app.logger.exception("Global relief failed")
        return jsonify({"error":"Global relief unavailable"}), 500




@app.route("/api/route-comparison")
def route_comparison():
    """Independent optional Phase 5 comparison; does not alter /api/mission-route."""
    try:
        from phase5_comparison import compare
        keys=("start_lat","start_lon","end_lat","end_lon")
        coords=[float(request.args[key]) for key in keys]
        result=compare(*coords)
        return jsonify(result), (200 if result["status"] in ("success","not_comparable") else 422)
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"status":"invalid_coordinates","error":str(exc)}),400
    except DEMValidationError as exc:
        return jsonify(status="dataset_unavailable", error=str(exc)), 503
    except rasterio.errors.RasterioIOError:
        app.logger.exception("Configured terrain dataset could not be opened")
        return jsonify(status="dataset_unavailable", error="Configured terrain data is unavailable. Check the dataset configuration."), 503
    except Exception:
        app.logger.exception("Phase 5 comparison failed")
        return jsonify({"status":"error","error":"Comparison failed; check server logs."}),500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
