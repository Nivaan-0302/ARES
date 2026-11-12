"""ARES coarse, global, DEM-derived navigation prototype.

The output is a *regional-scale illustrative corridor*, not a rover-safe route.
"""
import heapq
import math
from functools import lru_cache
import numpy as np
import rasterio
from rasterio.enums import Resampling
from terrain_region import DEM_PATH
from route_planner import calculate_route_distance

R = 3389.5
WIDTH, HEIGHT = 360, 180
COSTS = (1.0, 3.0, 8.0, 20.0)


def great_circle(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2-lat1
    dlon = (lon2-lon1+math.pi) % (2*math.pi)-math.pi
    x = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(min(1, math.sqrt(max(0, x))))


@lru_cache(maxsize=1)
def global_model():
    with rasterio.open(DEM_PATH) as ds:
        arr = ds.read(1, out_shape=(HEIGHT, WIDTH), resampling=Resampling.average, masked=True)
        elevations = np.ma.filled(arr.astype(np.float32), np.nan)
    # Preserve unknown regions as unavailable; avoid NaN propagation to adjacent cells.
    latitudes = 90-(np.arange(HEIGHT)+0.5)*180/HEIGHT
    dlat_m = math.pi*R*1000/HEIGHT
    dx = np.maximum(1000, (2*math.pi*R*1000/WIDTH)*np.cos(np.deg2rad(latitudes)))[:, None]
    valid = np.isfinite(elevations)
    filled = np.where(valid, elevations, 0)
    left = np.roll(filled, 1, axis=1)
    right = np.roll(filled, -1, axis=1)
    grad_x = (right-left)/(2*dx)
    grad_y = np.gradient(filled, dlat_m, axis=0)
    slopes = np.degrees(np.arctan(np.hypot(grad_x, grad_y)))
    good = valid & np.roll(valid, 1, axis=1) & np.roll(valid, -1, axis=1)
    good[1:-1] &= valid[:-2] & valid[2:]
    hazard = np.full((HEIGHT, WIDTH), -1, dtype=np.int8)
    hazard[good & (slopes <= 5)] = 0
    hazard[good & (slopes > 5) & (slopes <= 15)] = 1
    hazard[good & (slopes > 15) & (slopes <= 25)] = 2
    hazard[good & (slopes > 25)] = 3
    return elevations, hazard


def cell_for(lat, lon):
    if not all(map(math.isfinite, (lat, lon))) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('Coordinates must be finite and within Mars latitude/longitude bounds')
    return (min(HEIGHT-1, max(0, int((90-lat)*HEIGHT/180))),
            min(WIDTH-1, max(0, int((lon+180)*WIDTH/360))))


def position(cell):
    row, col = cell
    return [90-(row+0.5)*180/HEIGHT, -180+(col+0.5)*360/WIDTH]


def plan(start_lat, start_lon, end_lat, end_lon):
    _, hazard = global_model()
    start = cell_for(start_lat, start_lon)
    goal = cell_for(end_lat, end_lon)
    if hazard[start] < 0 or hazard[goal] < 0:
        return {'status':'no_data', 'message':'Coarse MOLA coverage unavailable at an endpoint.'}
    # A* on a longitude-wrapped global grid. Each edge is a physical great-circle distance.
    frontier = [(great_circle((start_lat, start_lon), (end_lat, end_lon)), 0., start)]
    best = {start:0.}
    previous = {}
    moves = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    expanded = 0
    while frontier:
        _, cost, current = heapq.heappop(frontier)
        if cost > best.get(current, math.inf)+1e-9:
            continue
        if current == goal:
            path = [current]
            while path[-1] in previous:
                path.append(previous[path[-1]])
            path.reverse()
            # Start and goal are real geographic coordinates, not cell centres.
            # Interior nodes retain coarse grid centres. This avoids two
            # artificial half-cell connectors at the endpoints.
            coords = [[start_lat, start_lon]] + [position(c) for c in path[1:-1]] + [[end_lat, end_lon]]
            # Short direct corridors may be represented by a single geodesic
            # when every sampled coarse cell is LOW hazard. Sample a great-circle
            # arc, including the dateline, instead of trusting grid-centre zigzags.
            if great_circle((start_lat,start_lon),(end_lat,end_lon)) < 300:
                lat_a, lon_a = math.radians(start_lat), math.radians(start_lon)
                lat_b, lon_b = math.radians(end_lat), math.radians(end_lon)
                def unit(lat,lon):
                    return (math.cos(lat)*math.cos(lon), math.cos(lat)*math.sin(lon), math.sin(lat))
                va,vb = unit(lat_a,lon_a),unit(lat_b,lon_b)
                angle = math.acos(max(-1,min(1,sum(x*y for x,y in zip(va,vb)))))
                clear = True
                for i in range(101):
                    t = i/100
                    if angle < 1e-10:
                        v = va
                    else:
                        x = math.sin((1-t)*angle)/math.sin(angle)
                        y = math.sin(t*angle)/math.sin(angle)
                        v = tuple(x*a+y*b for a,b in zip(va,vb))
                    lat = math.degrees(math.atan2(v[2],math.hypot(v[0],v[1])))
                    lon = math.degrees(math.atan2(v[1],v[0]))
                    if int(hazard[cell_for(lat,lon)]) != 0:
                        clear = False
                        break
                if clear:
                    coords = [[start_lat,start_lon],[end_lat,end_lon]]
            distance = round(calculate_route_distance(coords), 3)
            direct = round(great_circle((start_lat,start_lon),(end_lat,end_lon)), 3)
            # Geometry is an illustrative corridor through interior cell centres.
            # End cells are screened by the coarse hazard model, not continuously surveyed.
            counts = {name:0 for name in ('low','moderate','high','extreme')}
            names = ('low','moderate','high','extreme')
            for c in path:
                counts[names[int(hazard[c])]] += 1
            score = round(100*(counts['moderate']+3*counts['high']+6*counts['extreme'])/(6*len(path)),2)
            return {'status':'success','algorithm':'Global coarse-grid A*', 'route_type':'global_coarse_dem_scale',
                    'data_source':'NASA MOLA', 'grid_resolution_degrees':1,
                    'route_coordinates':coords, 'waypoint_count':len(coords),
                    'route_distance_km':distance,'direct_distance_km':direct,
                    'extra_distance_km':round(distance-direct,3),
                    'distance_increase_percent':round(100*(distance-direct)/direct,2) if direct else 0.,
                    'route_efficiency_percent':round(100*direct/distance,2) if distance else 100.,
                    'terrain_risk_score':score,'hazard_breakdown':counts,
                    'warning':'Illustrative 1-degree MOLA-derived corridor, not a validated rover-safe path.'}
        expanded += 1
        if expanded > WIDTH*HEIGHT:
            break
        r,c = current
        for dr,dc in moves:
            nr, nc = r+dr, (c+dc)%WIDTH
            if nr < 0 or nr >= HEIGHT or hazard[nr,nc] < 0:
                continue
            if dr and dc and (hazard[r,nc] < 0 or hazard[nr,c] < 0):
                continue
            neighbor = (nr,nc)
            current_position = (start_lat, start_lon) if current == start else position(current)
            next_position = (end_lat, end_lon) if neighbor == goal else position(neighbor)
            length = great_circle(current_position, next_position)
            edge_cost = length*COSTS[int(hazard[neighbor])]
            new_cost = cost + edge_cost
            if new_cost < best.get(neighbor, math.inf):
                best[neighbor] = new_cost
                previous[neighbor] = current
                heapq.heappush(frontier,(new_cost+great_circle(next_position,(end_lat,end_lon)),new_cost,neighbor))
    return {'status':'no_route','message':'No route found through the available coarse terrain grid.'}


def relief():
    elevations, _ = global_model()
    finite = np.isfinite(elevations)
    # Compact values for browser texture generation; avoid claiming this is photographic imagery.
    values = np.clip((np.where(finite,elevations,0)+9000)/30000,0,1)
    return {'width':WIDTH,'height':HEIGHT,'values':np.rint(values*255).astype(np.uint8).tolist(),
            'source':'NASA MOLA','rendering':'Elevation-coloured visualization, not photographic imagery'}
