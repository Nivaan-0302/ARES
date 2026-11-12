"""Single terrain-weighted routing workflow for coordinate and map selection.

MOLA-scale screening only. No guarantee of traversability or rover safety.
"""
import math
import numpy as np
from global_navigation import great_circle
from route_planner import astar_route, coordinates_to_grid, grid_route_to_coordinates, calculate_route_distance
from terrain_region import analyze_region
from route_refinement import refine_global_route, elevation_profile

HAZARD_NAMES = ('low', 'moderate', 'high', 'extreme')


def validate_coordinates(values):
    if len(values) != 4 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        raise ValueError('All four coordinates must be finite numbers.')
    a, b, c, d = values
    if not (-90 <= a <= 90 and -90 <= c <= 90 and -180 <= b <= 180 and -180 <= d <= 180):
        raise ValueError('Latitude must be -90 to 90; longitude must be -180 to 180.')
    return [float(v) for v in values]


def route_metrics(coords, start, end):
    if len(coords) < 2:
        raise ValueError('A route must contain at least two points.')
    if great_circle(coords[0], start) > 1e-5 or great_circle(coords[-1], end) > 1e-5:
        raise ValueError('Route geometry does not match the requested endpoints.')
    distance = calculate_route_distance(coords)
    direct = great_circle(start, end)
    if distance + 1e-5 < direct:
        raise ValueError('Route geometry is shorter than the great-circle distance.')
    return {'route_distance_km': round(distance, 3),
            'direct_distance_km': round(direct, 3),
            'extra_distance_km': round(max(0., distance-direct), 3),
            'distance_increase_percent': round(100 * max(0., distance-direct) / direct, 2) if direct else 0.,
            'route_efficiency_percent': round(100 * direct / distance, 2) if distance else 100.,
            'waypoint_count': len(coords)}


def regional_route(start, end, region):
    bounds = region['bounds']
    hazard = np.asarray(region['hazard_grid'], dtype=np.int8)
    s = coordinates_to_grid(*start, bounds, hazard.shape)
    g = coordinates_to_grid(*end, bounds, hazard.shape)
    if s is None or g is None:
        return None
    cells = astar_route(hazard, s, g, bounds=bounds)
    if not cells:
        return {'status': 'no_route', 'message': 'No regional route through available MOLA terrain cells.'}
    centres = grid_route_to_coordinates(cells, bounds, hazard.shape)
    # The original API used cell-centre endpoints; this created an inflated efficiency score.
    # Connect the actual user-selected endpoints to the computed cell-centre path.
    coords = [list(start), list(end)] if start == end else [list(start)] + centres + [list(end)]
    counts = {name: sum(int(hazard[r, c]) == i for r, c in cells)
              for i, name in enumerate(HAZARD_NAMES)}
    risk = round(100 * (counts['moderate'] + 3*counts['high'] + 6*counts['extreme']) / (6*len(cells)), 2)
    return {'status': 'success', 'algorithm': 'Regional terrain-weighted A*',
            'route_type': 'regional_dem_scale', 'data_source': 'NASA MOLA',
            'route_coordinates': coords, 'terrain_risk_score': risk,
            'hazard_breakdown': counts,
            'hazard_metric_scope': 'Regional A* path cells; heuristic classification, not measured rover risk',
            'refinement': {'sampled_windows': 1, 'modified_windows': 0, 'total_coarse_segments': 0,
                           'scope': 'One 0.5-degree regional window; path computed on DEM-derived hazard grid'},
            'warning': 'Regional MOLA-scale screening only. No rover-scale obstacle detection.'}


def make_scientific_report(result, coords):
    # All profile positions come from the exact route returned to both map renderers.
    try:
        samples = elevation_profile(coords, samples=25)
        elevations = [x['elevation_m'] for x in samples if x['elevation_m'] is not None]
    except (OSError, ValueError, IndexError) as exc:
        samples, elevations = [], []
        profile_error = str(exc)
    else:
        profile_error = None
    slopes = [x['slope_degrees'] for x in samples if x.get('slope_degrees') is not None]
    result['scientific_report'] = {
        'elevation_profile': samples,
        'minimum_elevation_m': min(elevations) if elevations else None,
        'maximum_elevation_m': max(elevations) if elevations else None,
        'elevation_sample_count': len(elevations),
        'slope_sample_count': len(slopes),
        'maximum_sampled_slope_degrees': max(slopes) if slopes else None,
        'mean_sampled_slope_degrees': round(sum(slopes)/len(slopes), 3) if slopes else None,
        'start_coordinates': coords[0], 'destination_coordinates': coords[-1],
        'direct_distance_km': result['direct_distance_km'],
        'route_distance_km': result['route_distance_km'],
        'route_efficiency_percent': result['route_efficiency_percent'],
        'hazard_breakdown': result['hazard_breakdown'],
        'terrain_risk_score': result['terrain_risk_score'],
        'hazard_metric_scope': result.get('hazard_metric_scope', 'Coarse 1-degree A* cells, not the full refined line'),
        'route_geometry': 'Exactly the polyline returned in route_coordinates',
        'sampled_route_coverage': result.get('refinement', {}).get('scope', 'Regional path cells'),
        'limitations': ('NASA MOLA elevations at approximately 463 m/pixel near the equator; '
                        '1-degree global planning averages out smaller hazards. Regional refinement samples only '
                        'selected windows. Slope categories are DEM-scale heuristics, not rover certification. '
                        'Risk is a waypoint-weighted index, not a probability of failure. '
                        + (f'Elevation profile unavailable: {profile_error}.' if profile_error else '')),
    }
    return result


def calculate_mission_route(start_lat, start_lon, end_lat, end_lon):
    a, b, c, d = validate_coordinates((start_lat, start_lon, end_lat, end_lon))
    start, end = [a, b], [c, d]
    # Regional planner is valid only when both endpoints fit in the same 0.5-degree window.
    # Boundary/polar cases transparently use global planning rather than failing the mission.
    nearby = abs(a-c) <= .24 and abs((b-d+180) % 360 - 180) <= .24
    result = None
    if nearby and abs(a) < 89.7 and abs(b) < 179.7:
        try:
            region = analyze_region(a, b)
            result = regional_route(start, end, region)
        except (ValueError, IndexError, OSError):
            pass
    if result is None:
        result = refine_global_route(a, b, c, d)
    if result.get('status') != 'success':
        return result
    coords = result['route_coordinates']
    result.update(route_metrics(coords, start, end))
    result['requested_start'] = start
    result['requested_destination'] = end
    return make_scientific_report(result, coords)
