"""Validated access to an externally supplied Mars elevation raster.

No dataset is downloaded or invented. Geographic Mars rasters and spherical
Mars equidistant-cylindrical rasters are supported. Elevations without a band
unit are explicitly assumed to be metres; known incompatible units are rejected.
"""
import math
import os
from pathlib import Path
import re
import weakref
from threading import RLock

import numpy as np
from geo_rules import align_longitude

DEM_PATH = Path(os.environ.get('ARES_DEM_PATH', str(
    Path(__file__).parent / 'data' / 'mola128_mola64_merge_90Nto90S_SimpleC_clon0.tif'
))).expanduser()


class DEMValidationError(RuntimeError):
    """An unavailable or scientifically incompatible DEM configuration."""


_READER_METADATA=weakref.WeakKeyDictionary()
_METADATA_LOCK=RLock()


def _axes(crs, params):
    radius = params.get('R')
    if radius is not None:
        return float(radius), float(radius)
    if params.get('a') is not None:
        a = float(params['a'])
        if params.get('b') is not None:
            return a, float(params['b'])
        if params.get('rf'):
            return a, a * (1 - 1 / float(params['rf']))
    # Named planetary ellipsoids may only expose their axes through WKT.
    match = re.search(r'(?:SPHEROID|ELLIPSOID)\s*\[\s*"[^"]*"\s*,\s*([0-9.eE+-]+)\s*,\s*([0-9.eE+-]+)', crs.to_wkt(), re.I)
    if not match:
        raise DEMValidationError('DEM CRS must identify its planetary reference ellipsoid.')
    a, inverse_flattening = map(float, match.groups())
    return a, a if inverse_flattening == 0 else a * (1 - 1 / inverse_flattening)


def validate_dem(ds):
    """Validate once per open, read-only Rasterio handle; never cache writers.

    A new open receives new validation. Weak keys do not retain raster handles,
    and copied dictionaries prevent callers from changing cached geometry.
    """
    cacheable=(type(ds).__module__.startswith('rasterio.')
               and getattr(ds,'mode',None)=='r' and not getattr(ds,'closed',True))
    if cacheable:
        with _METADATA_LOCK:
            cached=_READER_METADATA.get(ds)
        if cached is not None:
            return {**cached,'geographic_bounds':cached['geographic_bounds'].copy()}
    result=_validate_dem_uncached(ds)
    if cacheable:
        with _METADATA_LOCK:
            _READER_METADATA[ds]=result
    return {**result,'geographic_bounds':result['geographic_bounds'].copy()}


def _validate_dem_uncached(ds):
    """Return verified geometry/units metadata, or reject unsupported input."""
    if ds.crs is None:
        raise DEMValidationError('DEM has no CRS; supply a georeferenced Mars raster.')
    if ds.count < 1 or ds.width < 3 or ds.height < 3:
        raise DEMValidationError('DEM requires an elevation band and at least 3 by 3 pixels.')
    t = ds.transform
    if not all(math.isfinite(v) for v in (t.a,t.b,t.c,t.d,t.e,t.f,ds.bounds.left,ds.bounds.right,ds.bounds.top,ds.bounds.bottom)):
        raise DEMValidationError('DEM transform and extent must be finite.')
    if not (t.a > 0 and t.e < 0 and abs(t.b) < 1e-12 and abs(t.d) < 1e-12):
        raise DEMValidationError('DEM must be an axis-aligned, north-up raster.')
    params = ds.crs.to_dict()
    a, b = _axes(ds.crs, params)
    try:
        prime_meridian = float(params.get('pm',0))
    except (ValueError,TypeError) as exc:
        raise DEMValidationError('DEM must use the documented zero Mars prime meridian.') from exc
    if not math.isfinite(prime_meridian) or abs(prime_meridian) > 1e-12:
        raise DEMValidationError('Nonzero planetary prime meridians are unsupported.')
    if not all(math.isfinite(v) and 3_300_000 <= v <= 3_500_000 for v in (a, b)):
        raise DEMValidationError('DEM must use a Mars reference ellipsoid, not an Earth CRS.')
    if ds.crs.is_geographic:
        if not re.search(r'(?:ANGLEUNIT|UNIT)\s*\[\s*"degrees?"', ds.crs.to_wkt(), re.I):
            raise DEMValidationError('Geographic DEM angular coordinates must be in degrees.')
        geometry = {'kind': 'geographic', 'radius_m': (2*a+b)/3}
    elif params.get('proj') == 'eqc':
        if not math.isclose(a, b, rel_tol=1e-9):
            raise DEMValidationError('Projected DEM support requires spherical Mars equidistant cylindrical geometry.')
        if not (params.get('units') == 'm' or ('to_meter' in params and math.isclose(float(params['to_meter']),1.))):
            raise DEMValidationError('Projected DEM horizontal coordinates must be in metres.')
        values = {key: float(params.get(key, 0)) for key in ('lat_ts', 'lat_0', 'lon_0', 'x_0', 'y_0')}
        if not all(math.isfinite(v) for v in values.values()) or abs(values['lat_ts']) >= 90:
            raise DEMValidationError('Invalid equidistant cylindrical projection parameters.')
        geometry = {'kind': 'eqc', 'radius_m': a, **values}
    else:
        raise DEMValidationError('Unsupported DEM CRS: use Mars geographic degrees or spherical Mars equidistant cylindrical.')
    scales = getattr(ds, 'scales', (1.,))
    offsets = getattr(ds, 'offsets', (0.,))
    scale, offset = float(scales[0]), float(offsets[0])
    if not math.isfinite(scale) or scale <= 0 or not math.isfinite(offset):
        raise DEMValidationError('DEM elevation scale must be positive and scale/offset finite.')
    unit = (getattr(ds, 'units', (None,))[0] or '').strip().lower()
    if unit not in ('', 'm', 'meter', 'meters', 'metre', 'metres'):
        raise DEMValidationError('DEM elevation band must use metres.')
    geometry.update(elevation_scale=scale, elevation_offset=offset,
                    elevation_units='metres', elevation_units_assumed=not bool(unit),
                    crs=ds.crs.to_string(), width=ds.width, height=ds.height)
    west, south = _inverse(geometry, ds.bounds.left, ds.bounds.bottom)
    east, north = _inverse(geometry, ds.bounds.right, ds.bounds.top)
    tolerance = max(abs(north-south)/ds.height, 1e-7)
    longitude_tolerance=1.02*max(abs(east-west)/ds.width,1e-7)+1e-7
    if south < -90-tolerance or north > 90+tolerance or east-west > 360+longitude_tolerance:
        raise DEMValidationError('DEM extent is outside the supported Mars longitude/latitude domain.')
    geometry['geographic_bounds'] = {'west': west, 'south': south, 'east': east, 'north': north}
    return geometry



def validate_global_coverage(metadata):
    """Allow a bounded half-native-pixel registration discrepancy at each edge.

    The owner's 46081 x 23041 derivative is short of +180 by half a pixel
    and extends beyond -90 by a quarter pixel. A canonical target grid must
    be resampled by coordinates, never by stretching these native bounds.
    This validates an extent envelope, not the authenticity/completeness of data.
    """
    bounds = metadata['geographic_bounds']
    dx = (bounds['east']-bounds['west'])/metadata['width']
    dy = (bounds['north']-bounds['south'])/metadata['height']
    tx,ty = min(.01, .51*dx)+1e-9, min(.01, .51*dy)+1e-9
    origin = min((-180.,0.), key=lambda v:abs(bounds['west']-v))
    if (abs(bounds['west']-origin)>tx or abs(bounds['east']-(origin+360))>tx
            or abs(bounds['north']-90)>ty or abs(bounds['south']+90)>ty):
        raise DEMValidationError('Global navigation requires full 360-degree by 180-degree Mars coverage.')
    return {'canonical_west':origin, 'edge_tolerance_degrees':[tx,ty],
            'edge_offsets_degrees':{'west':bounds['west']-origin,
                'east':bounds['east']-(origin+360), 'north':bounds['north']-90,
                'south':bounds['south']+90}}

def _inverse(meta, x, y):
    if meta['kind'] == 'geographic':
        return float(x), float(y)
    radius = meta['radius_m']
    lon = meta['lon_0'] + math.degrees((x-meta['x_0']) / (radius*math.cos(math.radians(meta['lat_ts']))))
    lat = meta['lat_0'] + math.degrees((y-meta['y_0']) / radius)
    return lon, lat


def dataset_to_geographic(ds, x, y):
    """Return unwrapped longitude and latitude in degrees."""
    return _inverse(validate_dem(ds), x, y)


def geographic_to_dataset(ds, longitude, latitude):
    """Map degrees to native CRS, respecting a raster's longitude domain."""
    if not (math.isfinite(longitude) and math.isfinite(latitude) and -90 <= latitude <= 90):
        raise ValueError('Coordinates must be finite Mars longitude/latitude degrees.')
    meta = validate_dem(ds)
    bounds = meta['geographic_bounds']
    # Choose the equivalent longitude nearest the source raster's centre.
    lon = align_longitude(longitude,bounds['west'],bounds['east'])
    if bounds['east']-bounds['west']>359.98 and bounds['north']-bounds['south']>179.98:
        try:
            coverage=validate_global_coverage(meta)
        except DEMValidationError:
            pass
        else:
            # Full-world posting grids can contain both +/-180 seam samples.
            # Choose one canonical meridian, rather than selecting different
            # duplicate columns because the envelope is fractionally asymmetric.
            origin=coverage['canonical_west']
            lon=align_longitude(longitude,origin,origin+360)
    if meta['kind'] == 'geographic':
        return lon, latitude
    radius = meta['radius_m']
    return (meta['x_0'] + radius*math.radians(lon-meta['lon_0'])*math.cos(math.radians(meta['lat_ts'])),
            meta['y_0'] + radius*math.radians(latitude-meta['lat_0']))


def pixel_spacing_metres(ds, latitude):
    """Physical pixel spacing on the supported spherical/mean-radius model."""
    meta = validate_dem(ds)
    if meta['kind'] == 'geographic':
        angular_x, angular_y = math.radians(abs(ds.transform.a)), math.radians(abs(ds.transform.e))
    else:
        angular_x = abs(ds.transform.a)/(meta['radius_m']*math.cos(math.radians(meta['lat_ts'])))
        angular_y = abs(ds.transform.e)/meta['radius_m']
    return (meta['radius_m']*angular_x*abs(math.cos(math.radians(latitude))),
            meta['radius_m']*angular_y)


def read_elevation(ds, window=None, out_shape=None, resampling=None, boundless=False):
    """Read band masks, nodata, scales and offsets into masked metres."""
    meta = validate_dem(ds)
    kwargs = {'masked': True}
    if window is not None:
        kwargs['window'] = window
    if out_shape is not None:
        kwargs['out_shape'] = out_shape
    if resampling is not None:
        kwargs['resampling'] = resampling
    if boundless:
        kwargs['boundless'] = True
    raw = np.ma.asarray(ds.read(1, **kwargs), dtype=float)
    values = np.ma.masked_invalid(raw * meta['elevation_scale'] + meta['elevation_offset'])
    return values


def sample_point(ds, latitude, longitude):
    x, y = geographic_to_dataset(ds, longitude, latitude)
    row, col = ds.index(x, y)
    if not (0 <= row < ds.height and 0 <= col < ds.width):
        return None
    value = read_elevation(ds, window=((row,row+1),(col,col+1)))[0,0]
    return None if np.ma.is_masked(value) else float(value)


def slope_at_point(ds, latitude, longitude):
    x, y = geographic_to_dataset(ds, longitude, latitude)
    row, col = ds.index(x, y)
    if not (1 <= row < ds.height-1 and 1 <= col < ds.width-1):
        return None
    grid = read_elevation(ds, window=((row-1,row+2),(col-1,col+2)))
    # A central difference uses the centre plus four axial neighbours.
    # Missing diagonal samples do not invalidate unrelated derivatives.
    support = ((1,1),(0,1),(2,1),(1,0),(1,2))
    if grid.shape != (3,3) or any(np.ma.is_masked(grid[r,c]) for r,c in support):
        return None
    _,cell_latitude = dataset_to_geographic(ds,
        ds.transform.c+(col+.5)*ds.transform.a,
        ds.transform.f+(row+.5)*ds.transform.e)
    dx, dy = pixel_spacing_metres(ds, cell_latitude)
    if dx <= .001:
        return None
    gx, gy = (float(grid[1,2])-float(grid[1,0]))/(2*dx), (float(grid[2,1])-float(grid[0,1]))/(2*dy)
    return float(np.degrees(np.arctan(np.hypot(gx,gy))))


def classify_slopes(elevation, dx, dy, wrap_longitude=False):
    """Central/edge differences with valid centre and derivative-support masks."""
    z = np.ma.filled(np.ma.masked_invalid(np.ma.asarray(elevation, dtype=float)), np.nan)
    if z.ndim != 2 or min(z.shape) < 2:
        raise ValueError('Slope calculation requires at least two rows and columns.')
    if not math.isfinite(dy) or dy <= 0:
        raise ValueError('North-south pixel spacing must be finite and positive.')
    valid = np.isfinite(z)
    if wrap_longitude:
        gx = (np.roll(z,-1,axis=1)-np.roll(z,1,axis=1))/2
        support_x = np.roll(valid,-1,axis=1) & np.roll(valid,1,axis=1)
    else:
        gx = np.gradient(z, axis=1)
        support_x = np.empty_like(valid)
        support_x[:,1:-1] = valid[:,:-2] & valid[:,2:]
        support_x[:,0] = valid[:,0] & valid[:,1]
        support_x[:,-1] = valid[:,-1] & valid[:,-2]
    gy = np.gradient(z, axis=0)/dy
    support_y = np.empty_like(valid)
    support_y[1:-1] = valid[:-2] & valid[2:]
    support_y[0] = valid[0] & valid[1]
    support_y[-1] = valid[-1] & valid[-2]
    spacing = np.asarray(dx, dtype=float)
    if spacing.ndim == 1:
        spacing = spacing[:, None]

    with np.errstate(divide='ignore', invalid='ignore'):
        gx = gx / spacing
        slope = np.degrees(np.arctan(np.hypot(gx, gy)))

    good = valid & support_x & support_y & np.isfinite(slope) & (spacing > .001)

    hazard = np.full(z.shape, -1, dtype=np.int8)

    thresholds = np.array([5., 15., 25.])
    hazard[good] = np.digitize(
        np.round(slope[good], decimals=12),
        thresholds,
        right=True
    )

    return slope, hazard
