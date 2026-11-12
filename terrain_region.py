
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from pathlib import Path

DEM_PATH = (
    Path(__file__).parent
    / "data"
    / "mola128_mola64_merge_90Nto90S_SimpleC_clon0.tif"
)

MARS_RADIUS_M = 3389500


def analyze_region(latitude, longitude, radius_degrees=0.25):
    """
    Analyze a small region of Mars using NASA MOLA data.

    Returns a grid of DEM-scale slope classifications.
    """

    with rasterio.open(DEM_PATH) as dem:
        window = from_bounds(
            longitude - radius_degrees,
            latitude - radius_degrees,
            longitude + radius_degrees,
            latitude + radius_degrees,
            transform=dem.transform
        )

        # Round the window to whole raster pixels
        window = window.round_offsets().round_lengths()

        elevation = dem.read(1, window=window).astype(float)

        if elevation.size == 0:
            raise ValueError("No terrain data in selected region")

        elevation[elevation == dem.nodata] = np.nan

        # Approximate pixel spacing in metres
        dx = (
            dem.res[0]
            * np.pi / 180
            * MARS_RADIUS_M
            * np.cos(np.radians(latitude))
        )

        dy = (
            dem.res[1]
            * np.pi / 180
            * MARS_RADIUS_M
        )

        if dx <= 0.001:
            raise ValueError("Region too close to a pole")

        # Calculate terrain gradients
        gradient_y, gradient_x = np.gradient(elevation, dy, dx)

        slope = np.degrees(
            np.arctan(
                np.hypot(gradient_x, gradient_y)
            )
        )

        valid_slopes = slope[np.isfinite(slope)]

        if valid_slopes.size > 0:
            print("\nARES — SLOPE DIAGNOSTIC")
            print(f"Region: {latitude}, {longitude}")
            print(f"Pixel spacing X: {dx:.2f} metres")
            print(f"Pixel spacing Y: {dy:.2f} metres")
            print(f"Minimum slope: {np.min(valid_slopes):.4f}°")
            print(f"Average slope: {np.mean(valid_slopes):.4f}°")
            print(f"Maximum slope: {np.max(valid_slopes):.4f}°")


        # Terrain steepness categories
        hazard = np.full(slope.shape, -1, dtype=np.int8)

        hazard[np.isfinite(slope) & (slope <= 5)] = 0
        hazard[(slope > 5) & (slope <= 15)] = 1
        hazard[(slope > 15) & (slope <= 25)] = 2
        hazard[slope > 25] = 3

        
        # Geographic boundaries of the actual raster window
        actual_bounds = rasterio.windows.bounds(
            window,
            dem.transform
        )

        return {
            "latitude": latitude,
            "longitude": longitude,
            "bounds": {
                "west": actual_bounds[0],
                "south": actual_bounds[1],
                "east": actual_bounds[2],
                "north": actual_bounds[3]
            },
            "shape": list(hazard.shape),
            "hazard_grid": hazard.tolist(),
            "elevation_grid": [
                [
                    None if not np.isfinite(value) else float(value)
                    for value in row
                ]
                for row in elevation
            ],
            "classification": {
                "0": "LOW",
                "1": "MODERATE",
                "2": "HIGH",
                "3": "EXTREME",
                "-1": "NO DATA"
            }
        }
