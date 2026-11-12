
from flask import Flask, jsonify, request
import rasterio
import numpy as np
from terrain_region import analyze_region
from pathlib import Path
from route_planner import (
    astar_route,
    grid_route_to_coordinates,
    coordinates_to_grid,
    calculate_route_distance,

)
app = Flask(__name__, static_folder=".", static_url_path="")

DEM_PATH = (
    Path(__file__).parent
    / "data"
    / "mola128_mola64_merge_90Nto90S_SimpleC_clon0.tif"
)


@app.route("/")
def home():
    return app.send_static_file("index.html")


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
            row, col = dem.index(longitude, latitude)

            if not (0 <= row < dem.height and 0 <= col < dem.width):
                return jsonify({"error": "Location outside DEM"}), 400

            elevation = int(
                dem.read(
                    1,
                    window=((row, row + 1), (col, col + 1))
                )[0, 0]
            )

            if elevation == dem.nodata:
                return jsonify({"error": "No elevation data"}), 404

        return jsonify({
            "latitude": latitude,
            "longitude": longitude,
            "elevation_m": elevation,
            "source": "NASA MOLA Global DEM"
        })

    except (KeyError, ValueError):
        return jsonify({"error": "Provide valid lat and lon"}), 400

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
            row, col = dem.index(longitude, latitude)

            # A 3x3 neighborhood must fit inside the raster
            if not (1 <= row < dem.height - 1 and
                    1 <= col < dem.width - 1):
                return jsonify({
                    "error": "Location too close to dataset boundary"
                }), 400

            grid = dem.read(
                1,
                window=((row - 1, row + 2), (col - 1, col + 2))
            ).astype(float)

            if not np.all(np.isfinite(grid)) or np.any(grid == dem.nodata):
                return jsonify({
                    "error": "Missing terrain elevation data"
                }), 404

            pixel_width = (
                dem.res[0]
                * np.pi / 180
                * MARS_RADIUS_METRES
                * np.cos(np.radians(latitude))
            )

            pixel_height = (
                dem.res[1]
                * np.pi / 180
                * MARS_RADIUS_METRES
            )

            if pixel_width <= 0.001:
                return jsonify({
                    "error": "Slope calculation unavailable near poles"
                }), 400

            dz_dx = (
                grid[1, 2] - grid[1, 0]
            ) / (2 * pixel_width)

            dz_dy = (
                grid[2, 1] - grid[0, 1]
            ) / (2 * pixel_height)

            slope_degrees = float(
                np.degrees(
                    np.arctan(
                        np.hypot(dz_dx, dz_dy)
                    )
                )
            )

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
                "elevation_m": float(grid[1, 1]),
                "slope_degrees": round(slope_degrees, 3),
                "hazard_level": hazard_level,
                "method": "Central differences, 3x3 MOLA neighborhood",
                "source": "NASA MOLA Global DEM",
                "warning": "DEM-scale slope; not a rover-scale obstacle assessment"
            })

    except (KeyError, ValueError):
        return jsonify({
            "error": "Provide valid lat and lon"
        }), 400

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

        # Restrict requests to regions that fit inside the DEM
        if not (-89.75 <= latitude <= 89.75):
            return jsonify({"error": "Latitude outside supported range"}), 400

        if not (-179.75 <= longitude <= 179.75):
            return jsonify({"error": "Longitude outside supported range"}), 400

        result = analyze_region(
            latitude=latitude,
            longitude=longitude,
            radius_degrees=0.25
        )

        return jsonify(result)

    except (KeyError, ValueError):
        return jsonify({"error": "Provide valid lat and lon"}), 400

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

        coordinates = grid_route_to_coordinates(
            route, bounds, shape
        )

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



        route_distance_km = calculate_route_distance(coordinates)

       
        direct_distance_km = calculate_route_distance([
            coordinates[0],
            coordinates[-1]
        ])

        extra_distance_km = round(
            route_distance_km - direct_distance_km, 3
        )

        distance_increase_percent = round(
            (extra_distance_km / direct_distance_km) * 100,
            2
        ) if direct_distance_km > 0 else 0.0

        if route_distance_km > 0:
            route_efficiency_percent = round(
                min(100.0, direct_distance_km / route_distance_km * 100),
                2
            )
        else:
            route_efficiency_percent = 100.0



        return jsonify({
            "status": "success",
            "algorithm": "A*",
            "data_source": "NASA MOLA",
            "route_type": "regional_dem_scale",
            "start_cell": list(start),
            "goal_cell": list(goal),
            "waypoint_count": len(coordinates),
            "route_distance_km": route_distance_km,
            "route_efficiency_percent": route_efficiency_percent,
            "hazard_breakdown": hazard_counts,
            "terrain_risk_score": terrain_risk_score,
            "direct_distance_km": direct_distance_km,
            "extra_distance_km": extra_distance_km,
            "distance_increase_percent": distance_increase_percent,
            "route_coordinates": coordinates,
            "bounds": bounds
        })

    except (ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400

    except Exception:
        app.logger.exception("ARES route-planning error")
        return jsonify({
            "error": "Route calculation failed"
        }), 500


# ARES 3.0 — Coarse planet-wide routing and globe relief


@app.route("/api/mission-route")
def mission_route():
    """The single API used by map clicks and typed coordinates in both views."""
    from mission_routing import calculate_mission_route
    try:
        keys = ("start_lat", "start_lon", "end_lat", "end_lon")
        coords = [float(request.args[key]) for key in keys]
        result = calculate_mission_route(*coords)
        return jsonify(result), (200 if result.get("status") == "success" else 422)
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"status": "invalid_coordinates", "error": str(exc)}), 400
    except Exception:
        app.logger.exception("Mission route calculation failed")
        return jsonify({"status": "error", "error": "Mission routing failed; check server logs."}), 500

@app.route("/api/global-route")
def global_route():
    from global_navigation import plan
    try:
        keys = ("start_lat", "start_lon", "end_lat", "end_lon")
        coords = [float(request.args[key]) for key in keys]
        result = plan(*coords)
        return jsonify(result), (200 if result["status"] == "success" else 422)
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Global routing failed")
        return jsonify({"error":"Global routing failed"}), 500


@app.route("/api/refined-route")
def refined_route():
    from route_refinement import refine_global_route
    try:
        keys = ("start_lat", "start_lon", "end_lat", "end_lon")
        coords = [float(request.args[key]) for key in keys]
        result = refine_global_route(*coords)
        return jsonify(result), (200 if result["status"] == "success" else 422)
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Sampled global refinement failed")
        return jsonify({"error":"Sampled refinement failed"}), 500


@app.route("/api/global-relief")
def global_relief():
    from global_navigation import relief
    try:
        return jsonify(relief())
    except Exception:
        app.logger.exception("Global relief failed")
        return jsonify({"error":"Global relief unavailable"}), 500




@app.route("/api/route-comparison")
def route_comparison():
    """Independent optional Phase 5 comparison; does not alter /api/mission-route."""
    from phase5_comparison import compare
    try:
        keys=("start_lat","start_lon","end_lat","end_lon")
        coords=[float(request.args[key]) for key in keys]
        result=compare(*coords)
        return jsonify(result), (200 if result["status"] in ("success","not_comparable") else 422)
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"status":"invalid_coordinates","error":str(exc)}),400
    except Exception:
        app.logger.exception("Phase 5 comparison failed")
        return jsonify({"status":"error","error":"Comparison failed; check server logs."}),500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
