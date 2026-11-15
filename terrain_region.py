"""Regional slope screening on a validated, externally supplied Mars DEM."""
import math
import numpy as np
import rasterio
from rasterio.windows import Window, from_bounds

from dem_data import (DEM_PATH, validate_dem, geographic_to_dataset,
                      dataset_to_geographic, pixel_spacing_metres,
                      read_elevation, classify_slopes)

MARS_RADIUS_M = 3389500  # Mean-radius distance model used by route planning.


def analyze_region(latitude, longitude, radius_degrees=0.25):
    """Return DEM-scale classes; missing centres/support remain unavailable."""
    if not (math.isfinite(latitude) and math.isfinite(longitude) and
            -90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError('Provide finite Mars latitude/longitude coordinates.')
    if not math.isfinite(radius_degrees) or not 0 < radius_degrees <= .5:
        raise ValueError('Regional radius must be greater than zero and at most 0.5 degrees.')
    with rasterio.open(DEM_PATH) as dem:
        meta = validate_dem(dem)
        center_x, _ = geographic_to_dataset(dem, longitude, latitude)
        _, bottom = geographic_to_dataset(dem, longitude, max(-90.,latitude-radius_degrees))
        _, top = geographic_to_dataset(dem, longitude, min(90.,latitude+radius_degrees))
        factor = 1. if meta['kind'] == 'geographic' else (
            meta['radius_m']*math.pi/180*math.cos(math.radians(meta['lat_ts'])))
        # Construct around the native centre without accidentally wrapping one
        # side of a dateline-crossing window into the opposite side of the file.
        requested = from_bounds(center_x-radius_degrees*factor, bottom,
                                center_x+radius_degrees*factor, top,
                                transform=dem.transform).round_offsets().round_lengths()
        try:
            window = requested.intersection(Window(0,0,dem.width,dem.height))
        except rasterio.errors.WindowError as exc:
            raise ValueError('No terrain data in selected region') from exc
        # Keep the minimum two-cell footprint when clipping at a raster edge.
        # The outermost cell can still lack central-difference support.
        # Latitude is limited to the poles before window construction, so use
        # the unclipped diameter to check whether two rows were requested.
        y_per_degree = 1. if meta['kind'] == 'geographic' else meta['radius_m'] * math.pi / 180
        nominal_rows = math.floor(2 * radius_degrees * y_per_degree / abs(dem.transform.e) + .5)
        if min(window.width, window.height) < 2 <= min(requested.width, nominal_rows):
            width, height = max(2, window.width), max(2, window.height)
            if width <= dem.width and height <= dem.height:
                window = Window(min(window.col_off, dem.width - width),
                                min(window.row_off, dem.height - height),
                                width, height)
        if min(window.width, window.height) < 2:
            raise ValueError('Selected region contains too few pixels to calculate slope')
        # Read one native pixel of derivative support beyond the displayed
        # region. Boundless support is masked at the true dataset edge.
        halo = Window(window.col_off-1,window.row_off-1,window.width+2,window.height+2)
        padded = read_elevation(dem,window=halo,boundless=True)
        elevation = padded[1:-1,1:-1]
        if elevation.shape != (int(window.height),int(window.width)):
            raise ValueError('DEM read dimensions do not match the clipped region')
        actual = rasterio.windows.bounds(window, dem.transform)
        west,south = dataset_to_geographic(dem, actual[0],actual[1])
        east,north = dataset_to_geographic(dem, actual[2],actual[3])
        shift = 360*round((longitude-(west+east)/2)/360)
        west,east = west+shift,east+shift
        latitudes = north-(np.arange(elevation.shape[0])+.5)*(north-south)/elevation.shape[0]
        spacings = [pixel_spacing_metres(dem,float(lat)) for lat in latitudes]
        dx = np.asarray([value[0] for value in spacings])
        dy = spacings[0][1]
        halo_latitudes = north-(np.arange(elevation.shape[0]+2)-.5)*(north-south)/elevation.shape[0]
        halo_dx=np.asarray([pixel_spacing_metres(dem,float(lat))[0]
                            if -90<=lat<=90 else np.nan for lat in halo_latitudes])
        _,padded_hazard = classify_slopes(padded,halo_dx,dy)
        hazard=padded_hazard[1:-1,1:-1]
        data = np.ma.filled(elevation,np.nan)
        return {
            'latitude': latitude, 'longitude': longitude,
            'bounds': {'west':west,'south':south,'east':east,'north':north},
            'shape': list(hazard.shape), 'hazard_grid': hazard.tolist(),
            'elevation_grid': [[None if not np.isfinite(v) else float(v) for v in row] for row in data],
            'classification': {'0':'LOW','1':'MODERATE','2':'HIGH','3':'EXTREME','-1':'NO DATA'},
            'terrain_metadata': {
                'crs':meta['crs'], 'horizontal_model':meta['kind'],
                'elevation_units_assumed':meta['elevation_units_assumed'],
                'pixel_height_m':dy, 'pixel_width_range_m':[float(dx.min()),float(dx.max())],
                'slope_method':'Central axial differences at native pixel centres; one-pixel support halo; unknown support is unavailable',
                'distance_model':'Mean-radius sphere; source latitude convention must be documented',
                'window_clipped_to_dataset':window != requested,
            },
        }
