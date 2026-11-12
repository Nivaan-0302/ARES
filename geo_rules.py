"""Dependency-free coordinate conventions shared by terrain and route grids."""
import math


def align_longitude(longitude, west, east):
    """Choose the equivalent longitude nearest a window without edge clamping.

    Exact global +180 maps to -180; an incomplete raster's uncovered sliver
    remains uncovered. Subpixel numerical tolerances must not invent coverage.
    """
    if not all(math.isfinite(v) for v in (longitude, west, east)):
        raise ValueError('Longitude and bounds must be finite.')
    return longitude - 360 * math.floor((longitude - (west + east) / 2 + 180) / 360)


def contains_coordinate(latitude, longitude, bounds):
    """North-up pixel areas: west/north inclusive; east/south exclusive."""
    return (bounds['west'] <= longitude < bounds['east']
            and bounds['south'] < latitude <= bounds['north'])
