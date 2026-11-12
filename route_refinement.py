"""Bounded, local MOLA refinement of selected sections of a global corridor.

This is not continuous high-resolution global routing. The API reports coverage.
"""
import math
import numpy as np
import rasterio
from global_navigation import great_circle, plan
from route_planner import (astar_route, coordinates_to_grid,
                           grid_route_to_coordinates, calculate_route_distance)
from terrain_region import analyze_region, DEM_PATH

MAX_WINDOWS = 8
WEIGHTS = (0, 1, 3, 6)


def interpolate(a, b, t):
    """Interpolate longitude by the shortest wrapped direction."""
    dlon = (b[1] - a[1] + 180) % 360 - 180
    lon = (a[1] + dlon * t + 180) % 360 - 180
    return [a[0] + (b[0] - a[0]) * t, lon]


def grid_line(start, end):
    steps = max(abs(start[0]-end[0]), abs(start[1]-end[1]), 1)
    return [(round(start[0] + (end[0]-start[0])*i/steps),
             round(start[1] + (end[1]-start[1])*i/steps)) for i in range(steps+1)]


def cost_of(cells, hazard):
    return sum(WEIGHTS[int(hazard[r,c])] if hazard[r,c] >= 0 else 100 for r,c in cells)


def refine_segment(a, b):
    """Try a small MOLA A* detour near the midpoint of one coarse segment."""
    delta = max(abs(b[0]-a[0]), abs((b[1]-a[1]+180)%360-180))
    if delta < 0.015:
        return None
    half = min(.20, .10/delta)
    p = interpolate(a,b,.5-half)
    q = interpolate(a,b,.5+half)
    center = interpolate(a,b,.5)
    # The existing region reader does not wrap at the dateline or handle poles.
    if abs(center[0]) > 89.6 or abs(center[1]) > 179.65:
        return {'status':'skipped_boundary'}
    try:
        region = analyze_region(*center)
        grid = np.asarray(region['hazard_grid'], dtype=np.int8)
        bounds = region['bounds']
        s = coordinates_to_grid(*p, bounds, grid.shape)
        g = coordinates_to_grid(*q, bounds, grid.shape)
        if s is None or g is None:
            return {'status':'skipped_bounds'}
        original_cells = grid_line(s,g)
        old_cost = cost_of(original_cells, grid)
        route = astar_route(grid, s, g, bounds=bounds)
        if not route:
            return {'status':'no_local_route'}
        new_cost = cost_of(route, grid)
        old_dist = great_circle(p,q)
        replacement = [p] + grid_route_to_coordinates(route, bounds, grid.shape) + [q]
        new_dist = calculate_route_distance(replacement)
        old_hazard = max(int(grid[r,c]) for r,c in original_cells)
        new_hazard = max(int(grid[r,c]) for r,c in route)
        improved = (new_cost < old_cost and new_dist <= max(.1,old_dist)*1.5
                    and (old_hazard > new_hazard or new_cost <= old_cost*.75))
        return {'status':'refined' if improved else 'inspected',
                'replacement':replacement if improved else None,
                'highest_original_hazard':old_hazard,
                'highest_local_hazard':new_hazard,
                'regional_cells':len(route),
                'local_hazard_counts':{name:sum(int(grid[r,c])==i for r,c in route) for i,name in enumerate(('low','moderate','high','extreme'))},
                'center':center}
    except (ValueError, IndexError, RuntimeError, rasterio.errors.RasterioError) as exc:
        return {'status':'unavailable','reason':str(exc)}


def elevation_profile(coordinates, samples=20):
    """Sample elevation from the native MOLA raster at spaced route positions."""
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
        readings = dem.sample([(p[1],p[0]) for p in points], masked=True)
        values = []
        for sample in readings:
            val = sample[0]
            values.append(None if np.ma.is_masked(val) or not np.isfinite(val) or val == dem.nodata else float(val))
        slopes = []
        for lat, lon in points:
            row, col = dem.index(lon, lat)
            if not (1 <= row < dem.height-1 and 1 <= col < dem.width-1):
                slopes.append(None)
                continue
            cell = dem.read(1, window=((row-1,row+2),(col-1,col+2))).astype(float)
            if np.any(~np.isfinite(cell)) or (dem.nodata is not None and np.any(cell == dem.nodata)):
                slopes.append(None)
                continue
            dx = abs(dem.res[0]) * math.pi / 180 * 3389500 * abs(math.cos(math.radians(lat)))
            dy = abs(dem.res[1]) * math.pi / 180 * 3389500
            if dx < .001:
                slopes.append(None)
                continue
            gradient_x = (cell[1,2]-cell[1,0])/(2*dx)
            gradient_y = (cell[2,1]-cell[0,1])/(2*dy)
            slopes.append(round(math.degrees(math.atan(math.hypot(gradient_x,gradient_y))),3))
    return [{'distance_km':round(t,2),'latitude':round(p[0],5),
             'longitude':round(p[1],5),'elevation_m':v,'slope_degrees':slope}
            for t,p,v,slope in zip(targets,points,values,slopes)]


def refine_global_route(start_lat,start_lon,end_lat,end_lon):
    base = plan(start_lat,start_lon,end_lat,end_lon)
    if base['status'] != 'success':
        return base
    coords = base['route_coordinates']
    segments = len(coords)-1
    chosen = sorted(set(round(i*(segments-1)/max(1,min(MAX_WINDOWS,segments)-1))
                        for i in range(min(MAX_WINDOWS,segments)))) if segments else []
    revised = [coords[0]]
    inspected = 0
    changed = 0
    results = []
    for idx in range(segments):
        if idx in chosen:
            result = refine_segment(coords[idx],coords[idx+1])
            if result is not None:
                inspected += 1
                results.append({'segment':idx,'status':result['status'],
                                'center':result.get('center'),
                                'highest_original_hazard':result.get('highest_original_hazard'),
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
    distance = calculate_route_distance(cleaned)
    direct = base['direct_distance_km']
    coarse_distance = base["route_distance_km"]
    base.update(route_coordinates=cleaned,waypoint_count=len(cleaned),
                route_distance_km=round(max(distance,direct),3),
                extra_distance_km=round(max(0,distance-direct),3),
                route_efficiency_percent=round(100*direct/max(distance,direct),2) if distance else 100,
                route_type='global_sampled_local_refinement',
                algorithm='Coarse global A* + bounded regional A* checks')
    base['refinement'] = {'sampled_windows':inspected,'modified_windows':changed,
                          'total_coarse_segments':segments,
                          'inspected_segment_fraction':round(inspected/max(1,segments),3),
                          'windows':results,
                          'scope':'Selected route sections only; unsampled terrain is not validated',
                          'coarse_route_distance_km':coarse_distance,
                          'refined_route_distance_km':round(max(distance,direct),3)}
    try:
        profile = elevation_profile(cleaned)
        elevations = [x['elevation_m'] for x in profile if x['elevation_m'] is not None]
        base['scientific_report'] = {
            'elevation_profile':profile,
            'minimum_elevation_m':min(elevations) if elevations else None,
            'maximum_elevation_m':max(elevations) if elevations else None,
            'elevation_sample_count':len(elevations),
            'coarse_hazard_breakdown':base['hazard_breakdown'],
            'limitations':'1° global DEM and at most 8 sampled 0.5° regional windows; MOLA is not rover-scale safety data. Hazard counts and risk index are coarse and do not represent full high-resolution route exposure.'}
    except (OSError,ValueError,rasterio.errors.RasterioError) as exc:
        base['scientific_report'] = {'elevation_profile':[], 'limitations':f'Elevation profile unavailable: {exc}. Route safety has not been validated.'}
    base['warning'] = 'Sampled local refinements only; no continuous rover-safe corridor validation.'
    return base
