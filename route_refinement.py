"""Bounded, local MOLA refinement of selected sections of a global corridor.

This is not continuous high-resolution global routing. The API reports coverage.
"""
import math
import logging
import numpy as np
import rasterio
from global_navigation import great_circle, plan
from route_planner import (astar_route, coordinates_to_grid,
                           grid_route_with_endpoints, calculate_route_distance,
                           great_circle_interpolate, hazard_cell_mask)
from terrain_region import analyze_region, DEM_PATH
from dem_data import DEMValidationError, validate_dem, sample_point, slope_at_point

MAX_WINDOWS = 8
WEIGHTS = (0, 1, 3, 6)


def interpolate(a, b, t):
    """Interpolate along the same spherical arc used by route distances."""
    return great_circle_interpolate(a, b, t)


def grid_line(start, end):
    steps = max(abs(start[0]-end[0]), abs(start[1]-end[1]), 1)
    return [(round(start[0] + (end[0]-start[0])*i/steps),
             round(start[1] + (end[1]-start[1])*i/steps)) for i in range(steps+1)]


def cost_of(cells, hazard):
    return sum(WEIGHTS[int(hazard[r,c])] if hazard[r,c] in (0,1,2,3) else 100 for r,c in cells)


def refine_segment(a, b):
    """Try a small MOLA A* detour near the midpoint of one coarse segment."""
    delta = max(abs(b[0]-a[0]), abs((b[1]-a[1]+180)%360-180))
    if delta < 0.015:
        return {'status': 'skipped_short_segment'}
    half = min(.20, .10/delta)
    p = interpolate(a,b,.5-half)
    q = interpolate(a,b,.5+half)
    center = interpolate(a,b,.5)
    # The existing region reader does not wrap at the dateline or handle poles.
    if abs(center[0]) > 89.6 or abs(center[1]) > 179.65:
        return {'status':'skipped_boundary', 'center':center}
    try:
        region = analyze_region(*center)
        grid = np.asarray(region['hazard_grid'])
        available=hazard_cell_mask(grid)
        if not available.any():
            return {'status':'unavailable', 'center':center,
                    'reason':'No classified terrain cells in the local window.'}
        bounds = region['bounds']
        s = coordinates_to_grid(*p, bounds, grid.shape)
        g = coordinates_to_grid(*q, bounds, grid.shape)
        if s is None or g is None:
            return {'status':'skipped_bounds', 'center':center}
        original_cells = grid_line(s,g)
        old_cost = cost_of(original_cells, grid)
        route = astar_route(grid, s, g, bounds=bounds)
        if not route:
            return {'status':'no_local_route', 'center':center}
        new_cost = cost_of(route, grid)
        old_dist = great_circle(p,q)
        replacement = grid_route_with_endpoints(route, bounds, grid.shape, p, q)
        new_dist = calculate_route_distance(replacement, round_digits=None)
        old_hazard = max((int(grid[r,c]) for r,c in original_cells if available[r,c]),default=-1)
        old_unknown = any(not available[r,c] for r,c in original_cells)
        new_hazard = max(int(grid[r,c]) for r,c in route)
        improved = (new_cost < old_cost and new_dist <= max(.1,old_dist)*1.5
                    and (old_hazard > new_hazard or new_cost <= old_cost*.75))
        return {'status':'refined' if improved else 'inspected',
                'replacement':replacement if improved else None,
                'highest_original_hazard':old_hazard,
                'original_contains_unknown':old_unknown,
                'highest_local_hazard':new_hazard,
                'regional_cells':len(route),
                'local_hazard_counts':{name:sum(int(grid[r,c])==i for r,c in route) for i,name in enumerate(('low','moderate','high','extreme'))},
                'center':center}
    except (OSError, ValueError, IndexError, RuntimeError, rasterio.errors.RasterioError) as exc:
        logging.getLogger(__name__).warning('Local refinement data unavailable',exc_info=True)
        return {'status':'unavailable','reason':'Local terrain data unavailable; see server logs', 'center':center}


def elevation_profile(coordinates, samples=20):
    """Sample native DEM values at evenly spaced spherical route positions.

    Elevation and slope are sparse DEM-scale samples, not a continuous survey.
    Shared DEM helpers enforce the supported CRS, transforms, units and masks.
    """
    if len(coordinates) < 2:
        raise ValueError('An elevation profile requires at least two route points.')
    if not isinstance(samples, int) or isinstance(samples, bool) or samples < 2:
        raise ValueError('An elevation profile requires at least two samples.')
    lengths = [great_circle(a,b) for a,b in zip(coordinates,coordinates[1:])]
    total = sum(lengths)
    targets = [total*i/(samples-1) for i in range(samples)]
    points = []
    for target in targets:
        acc = 0
        for idx,length in enumerate(lengths):
            if acc+length >= target or idx == len(lengths)-1:
                points.append(interpolate(coordinates[idx],coordinates[idx+1],
                                          min(1,max(0,(target-acc)/length)) if length else 0))
                break
            acc += length
    with rasterio.open(DEM_PATH) as dem:
        validate_dem(dem)
        values = [sample_point(dem, lat, lon) for lat, lon in points]
        slopes = [slope_at_point(dem, lat, lon) for lat, lon in points]
    return [{'distance_km':round(t,2),'latitude':round(p[0],5),
             'longitude':round(p[1],5),'elevation_m':v,'slope_degrees':slope}
            for t,p,v,slope in zip(targets,points,values,slopes)]


def refine_global_route(start_lat,start_lon,end_lat,end_lon, *, include_profile=True):
    base = plan(start_lat,start_lon,end_lat,end_lon)
    if base['status'] != 'success':
        return base
    coords = base['route_coordinates']
    segments = len(coords)-1
    chosen = sorted(set(round(i*(segments-1)/max(1,min(MAX_WINDOWS,segments)-1))
                        for i in range(min(MAX_WINDOWS,segments)))) if segments else []
    revised = [coords[0]]
    attempted = 0
    inspected = 0
    skipped = 0
    unavailable = 0
    changed = 0
    results = []
    for idx in range(segments):
        if idx in chosen:
            attempted += 1
            result = refine_segment(coords[idx],coords[idx+1])
            if result is None:
                result = {'status': 'skipped_short_segment'}
            if result is not None:
                status = result['status']
                inspected += status in ('refined', 'inspected', 'no_local_route')
                skipped += status.startswith('skipped_')
                unavailable += status == 'unavailable'
                results.append({'segment':idx,'status':result['status'],
                                'center':result.get('center'),
                                'reason':result.get('reason'),
                                'highest_original_hazard':result.get('highest_original_hazard'),
                                'original_contains_unknown':result.get('original_contains_unknown'),
                                'highest_local_hazard':result.get('highest_local_hazard'),
                                'local_hazard_counts':result.get('local_hazard_counts')})
                if result['status']=='refined':
                    revised.extend(result['replacement'])
                    changed += 1
        revised.append(coords[idx+1])
    # Eliminate adjacent duplicate points, including coincident start/end points.
    cleaned = [revised[0]]
    for p in revised[1:]:
        if great_circle(cleaned[-1],p)>1e-7:
            cleaned.append(p)
    if len(cleaned)<2:
        cleaned.append(coords[-1])
    distance = calculate_route_distance(cleaned, round_digits=None)
    direct = great_circle((start_lat, start_lon), (end_lat, end_lon))
    coarse_distance = base["route_distance_km"]
    base.update(route_coordinates=cleaned,waypoint_count=len(cleaned),
                route_distance_km=round(distance,3),
                direct_distance_km=round(direct,3),
                extra_distance_km=round(max(0,distance-direct),3),
                distance_increase_percent=round(100*max(0,distance-direct)/direct,2) if direct else 0.,
                route_efficiency_percent=round(100*direct/max(distance,direct),2) if distance else 100,
                hazard_metric_scope='Coarse 1-degree A* cells; local refinement does not rescore full route exposure',
                route_type='global_sampled_local_refinement',
                algorithm='Coarse global A* + bounded regional A* checks')
    base['refinement'] = {'attempted_windows':attempted,'sampled_windows':inspected,
                          'skipped_windows':skipped,'unavailable_windows':unavailable,
                          'modified_windows':changed,
                          'total_coarse_segments':segments,
                          'inspected_segment_fraction':round(inspected/max(1,segments),3),
                          'windows':results,
                          'scope':'Selected local windows only; inspected segment fraction counts segments with a sampled window, not continuous terrain coverage',
                          'coarse_route_distance_km':coarse_distance,
                          'refined_route_distance_km':round(distance,3)}
    base['warning'] = 'Sampled local refinements only; no continuous rover-safe corridor validation.'
    if not include_profile:
        return base
    try:
        profile = elevation_profile(cleaned)
        elevations = [x['elevation_m'] for x in profile if x['elevation_m'] is not None]
        base['scientific_report'] = {
            'elevation_profile':profile,
            'minimum_elevation_m':min(elevations) if elevations else None,
            'maximum_elevation_m':max(elevations) if elevations else None,
            'elevation_sample_count':len(elevations),
            'coarse_hazard_breakdown':base['hazard_breakdown'],
            'limitations':'1° global DEM and at most 8 sampled 0.5° regional windows; MOLA is not rover-scale safety data. Coarse means can exclude masked native samples and do not certify continuous coverage. Hazard counts and risk index are coarse and do not represent full high-resolution route exposure.'}
    except (OSError,ValueError,DEMValidationError,rasterio.errors.RasterioError) as exc:
        logging.getLogger(__name__).warning('Refined-route elevation profile unavailable',exc_info=True)
        base['scientific_report'] = {'elevation_profile':[], 'limitations':'Elevation profile unavailable: native terrain data could not be read. Route safety has not been validated.'}
    return base
