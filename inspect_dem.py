
import rasterio
from pathlib import Path

# Locate the NASA MOLA elevation dataset
data_folder = Path(__file__).parent / "data"
tiff_files = list(data_folder.glob("*.tif"))

if not tiff_files:
    print("ERROR: No TIFF file found in the data folder.")
    raise SystemExit(1)

dem_path = tiff_files[0]

print("ARES — NASA MOLA DATASET INSPECTION")
print("-----------------------------------")

with rasterio.open(dem_path) as dem:
    print("Filename:", dem_path.name)
    print("Width:", dem.width, "pixels")
    print("Height:", dem.height, "pixels")
    print("Bands:", dem.count)
    print("Data type:", dem.dtypes[0])
    print("Coordinate system:", dem.crs)
    print("Bounds:", dem.bounds)
    print("Pixel resolution:", dem.res)
    print("NoData value:", dem.nodata)
    print("Band units:", dem.units)
    print("Scale:", dem.scales)
    print("Offset:", dem.offsets)

print("-----------------------------------")
print("Inspection complete.")


# Read a sample elevation at the Martian equator

sample_latitude = 0.0
sample_longitude = 0.0

with rasterio.open(dem_path) as dem:
    row, col = dem.index(
        sample_longitude,
        sample_latitude
    )

    elevation = dem.read(
        1,
        window=((row, row + 1), (col, col + 1))
    )[0, 0]

    print()
    print("ARES — MARTIAN ELEVATION TEST")
    print("-----------------------------")
    print("Latitude:", sample_latitude)
    print("Longitude:", sample_longitude)

    if elevation == dem.nodata:
        print("Elevation: No data available")
    else:
        print("Raw elevation value:", int(elevation))


# ARES — Local Martian Terrain Slope Analysis

import numpy as np

MARS_RADIUS_METRES = 3389500

with rasterio.open(dem_path) as dem:
    latitude = 0.0
    longitude = 0.0

    row, col = dem.index(longitude, latitude)

    # Read a 3 × 3 elevation grid around the location
    elevation_grid = dem.read(
        1,
        window=((row - 1, row + 2), (col - 1, col + 2))
    ).astype(float)

    nodata = dem.nodata

    if elevation_grid.shape != (3, 3) or np.any(elevation_grid == nodata):
        print("Cannot calculate slope: missing or incomplete elevation data.")
    else:
        # Convert angular pixel spacing into approximate metres
        degrees_to_radians = np.pi / 180

        pixel_width_metres = (
            dem.res[0]
            * degrees_to_radians
            * MARS_RADIUS_METRES
            * np.cos(np.radians(latitude))
        )

        pixel_height_metres = (
            dem.res[1]
            * degrees_to_radians
            * MARS_RADIUS_METRES
        )

        # Central differences in east-west and north-south directions
        dz_dx = (
            elevation_grid[1, 2] - elevation_grid[1, 0]
        ) / (2 * pixel_width_metres)

        dz_dy = (
            elevation_grid[2, 1] - elevation_grid[0, 1]
        ) / (2 * pixel_height_metres)

        slope_radians = np.arctan(
            np.sqrt(dz_dx ** 2 + dz_dy ** 2)
        )

        slope_degrees = np.degrees(slope_radians)

        print()
        print("ARES — MARTIAN TERRAIN ANALYSIS")
        print("--------------------------------")
        print("Latitude:", latitude)
        print("Longitude:", longitude)
        print("Centre elevation:", elevation_grid[1, 1], "m")
        print("Approximate pixel width:", round(pixel_width_metres, 2), "m")
        print("Approximate pixel height:", round(pixel_height_metres, 2), "m")
        print("Estimated terrain slope:", round(slope_degrees, 3), "degrees")
