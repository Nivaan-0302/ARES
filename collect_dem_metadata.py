"""Print a read-only metadata packet for the user's original Mars DEM.

Example: python collect_dem_metadata.py /path/to/original.tif --sha256
No elevation data is changed or copied. The optional checksum streams the file.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raster", type=Path, help="Original GeoTIFF path; it is opened read-only")
    parser.add_argument("--sha256", action="store_true", help="Read the entire file to calculate its checksum")
    args = parser.parse_args()
    import rasterio
    with rasterio.open(args.raster) as ds:
        packet = {
            "filename": args.raster.name,
            "size_bytes": args.raster.stat().st_size,
            "driver": ds.driver, "width": ds.width, "height": ds.height,
            "band_count": ds.count, "dtypes": ds.dtypes,
            "crs": ds.crs.to_string() if ds.crs else None,
            "crs_wkt": ds.crs.to_wkt() if ds.crs else None,
            "transform": list(ds.transform), "bounds": list(ds.bounds),
            "resolution": ds.res, "nodata": ds.nodatavals,
            "units": ds.units, "scales": ds.scales, "offsets": ds.offsets,
            "mask_flags": [[flag.name for flag in flags] for flags in ds.mask_flag_enums],
            "overview_factors": ds.overviews(1) if ds.count else [],
            "dataset_tags": ds.tags(), "band_1_tags": ds.tags(1) if ds.count else {},
            "software": {"rasterio": rasterio.__version__, "gdal": rasterio.__gdal_version__},
            "source_url": "User must supply the original product/download URL separately",
            "preprocessing": "User must describe any reprojection, cropping, resampling or conversion separately",
        }
    if args.sha256:
        digest = hashlib.sha256()
        with args.raster.open("rb") as stream:
            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
        packet["sha256"] = digest.hexdigest()
    print(json.dumps(_json_safe(packet), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
