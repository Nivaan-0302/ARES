"""ARES coarse, global, DEM-derived navigation prototype.

The output is a *regional-scale illustrative corridor*, not a rover-safe route.
"""
import heapq
import math
from functools import lru_cache
from threading import Lock
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from affine import Affine
from dem_data import DEM_PATH, DEMValidationError, validate_dem, validate_global_coverage, read_elevation, classify_slopes
from route_planner import calculate_route_distance
from geo_rules import align_longitude

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


_MODEL_LOCK = Lock()


def global_model():
    """Share one bounded model per current dataset identity, including cold loads."""
    try:
        info = DEM_PATH.stat()
    except OSError as exc:
        raise DEMValidationError('Configured DEM is unavailable; set ARES_DEM_PATH to a readable Mars raster.') from exc
    identity = (str(DEM_PATH.resolve()), info.st_size, info.st_mtime_ns)
    with _MODEL_LOCK:
        return _cached_global_model(identity)


@lru_cache(maxsize=1)
def _cached_global_model(identity):
    with rasterio.open(identity[0]) as ds:
        meta = validate_dem(ds)
        bounds = meta['geographic_bounds']
        coverage=validate_global_coverage(meta)
        west=coverage['canonical_west']
        if meta['kind']=='geographic':
            x0,y0,dx,dy=west,90.,1.,1.
        else:
            factor=meta['radius_m']*math.pi/180
            dx=factor*math.cos(math.radians(meta['lat_ts']));dy=factor
            x0=meta['x_0']+(west-meta['lon_0'])*dx
            y0=meta['y_0']+(90-meta['lat_0'])*dy
        target=Affine(dx,0,x0,0,-dy,y0)
        # Warp by actual geographic coordinates onto the canonical 1-degree
        # grid. Resizing the native envelope would shift/stretch the owner's
        # subpixel-offset derivative. Original pixels are never changed.
        with WarpedVRT(ds,crs=ds.crs,transform=target,width=WIDTH,height=HEIGHT,
                       resampling=Resampling.average,dtype='float64',nodata=np.nan) as vrt:
            raw=np.ma.masked_invalid(vrt.read(1,masked=True))
            elevations=np.ma.filled(raw*meta['elevation_scale']+meta['elevation_offset'],np.nan)
        if west==0:
            elevations = np.roll(elevations, WIDTH//2, axis=1)
    latitudes = 90-(np.arange(HEIGHT)+0.5)*180/HEIGHT
    dy = math.pi*meta['radius_m']/HEIGHT
    dx = (2*math.pi*meta['radius_m']/WIDTH)*np.cos(np.deg2rad(latitudes))
    _,hazard = classify_slopes(elevations, dx, dy, wrap_longitude=True)
    return elevations, hazard


global_model.cache_clear = _cached_global_model.cache_clear


def cell_for(lat, lon):
    if not all(map(math.isfinite, (lat, lon))) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('Coordinates must be finite and within Mars latitude/longitude bounds')
    lon=align_longitude(lon,-180.,180.)
    # Exact poles use the adjoining coarse latitude band; longitude is physically
    # degenerate there. This global spherical convention does not clamp a cropped
    # native raster's east/south edges or supply a missing native elevation.
    return (min(HEIGHT-1, max(0, int((90-lat)*HEIGHT/180))),
            min(WIDTH-1, max(0, int((lon+180)*WIDTH/360))))


def position(cell):
    row, col = cell
    return [90-(row+0.5)*180/HEIGHT, -180+(col+0.5)*360/WIDTH]


def _low_corridor_between(a,b,hazard):
    """Conservative coarse-grid cover between adjacent geodesic samples.

    At high latitude even a short physical step crosses many longitude cells.
    Screen the wrapped bounding cells and one-cell halo, rather than skipping
    unknown terrain between the fixed geodesic samples. This is coarse screening,
    not a claim of native-resolution continuous safety.
    """
    r0,c0=cell_for(*a);r1,c1=cell_for(*b)
    dc=(c1-c0+WIDTH//2)%WIDTH-WIDTH//2
    rows=range(max(0,min(r0,r1)-1),min(HEIGHT,max(r0,r1)+2))
    cols=[c%WIDTH for c in range(min(c0,c0+dc)-1,max(c0,c0+dc)+2)]
    return bool(np.all(hazard[np.ix_(list(rows),cols)]==0))


def plan(start_lat, start_lon, end_lat, end_lon):
    start = cell_for(start_lat, start_lon)
    goal = cell_for(end_lat, end_lon)
    _, hazard = global_model()
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
                previous_sample = None
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
                    sample=(lat,lon)
                    if (int(hazard[cell_for(lat,lon)]) != 0 or
                        (previous_sample is not None and not _low_corridor_between(previous_sample,sample,hazard))):
                        clear = False
                        break
                    previous_sample=sample
                if clear:
                    coords = [[start_lat,start_lon],[end_lat,end_lon]]
            distance = calculate_route_distance(coords, round_digits=None)
            direct = great_circle((start_lat,start_lon),(end_lat,end_lon))
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
                    'route_distance_km':round(distance,3),'direct_distance_km':round(direct,3),
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
