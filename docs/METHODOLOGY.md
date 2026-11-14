# Scientific methodology

ARES turns an externally configured Mars elevation raster into terrain observations and illustrative slope classes. It keeps input measurements, numerical estimates and planning assumptions distinct. Read [scientific inputs](SCIENTIFIC_INPUTS.md), [recorded validation](SCIENTIFIC_VALIDATION.md) and [limitations](LIMITATIONS.md) alongside this method.

## Data and spatial scale

The scientific foundation is Mars Global Surveyor's Mars Orbiter Laser Altimeter (MOLA). The cited native product family is Smith and colleagues (2003), *Mars Global Surveyor Laser Altimeter Mission Experiment Gridded Data Record*, `MGS-M-MOLA-5-MEGDR-L3-V1.0`, [NASA Planetary Data System](https://pds.nasa.gov/ds-view/pds/viewProfile.jsp?dsid=MGS-M-MOLA-5-MEGDR-L3-V1.0). Gridded elevations can include interpolated bins; a valid grid cell is not necessarily an individual laser observation.

ARES's original local GeoTIFF is a MOLA-derived product, distinct from an authoritative native PDS label. Its recorded geometry is 46,081 × 23,041 pixels at approximately 0.00781225° spacing. Near the equator that spacing is about 462 m under ARES's mean-radius model. Longitude spacing in metres decreases toward the poles. These pixels cannot resolve wheel-scale rocks, small craters, cracks or human-scale obstacles. File identity, conversion history and vertical reference are separate questions: see [dataset provenance](DATASET_PROVENANCE.md).

The optional public 4 samples/degree PDS reference is a different input, converted without resampling by [prepare_global_reference.py](../scripts/prepare_global_reference.py). Its native spacing is approximately 14.8 km north–south. It exercises the same processing pipeline at a coarser scale; it must not be presented as the original high-resolution DEM.

NASA Trek Viking MDIM21 map imagery and the NASA/JPL-Caltech hero mosaic provide visual context. They do not supply the elevation values used by the algorithms. See [asset provenance](../ASSET_PROVENANCE.md).

## Read-only input validation

[dem_data.py](../dem_data.py) reads the raster named by `ARES_DEM_PATH`, or the documented local default. It checks:

- A nonempty elevation band, at least 3 × 3 pixels, finite geometry and an axis-aligned north-up transform.
- Mars-sized reference axes and the supported zero prime meridian; Earth CRS inputs are rejected.
- Geographic angular coordinates in degrees, or supported spherical Mars equidistant-cylindrical coordinates in metres.
- Finite positive elevation scale and finite offset. Explicit non-metre band units are rejected; missing units are disclosed as `elevation_units_assumed: true`.

The first band is read with Rasterio masks and NoData, then transformed by `elevation = stored_value × scale + offset`. Nonfinite results remain masked. Neither an absent unit nor a horizontal CRS is proof of the vertical datum. Source files are not modified or redistributed by this process.

## Coordinates and elevation sampling

UI/API points use `[latitude, longitude]` in degrees. Raster transforms use `(x, y)`, hence `(longitude, latitude)` for geographic input. [geo_rules.py](../geo_rules.py) and the DEM helpers align equivalent longitudes to the input's domain; they do not fill an uncovered interval.

A point lookup returns the value of the containing native pixel without interpolation. West and north pixel-area edges are included; east and south edges are excluded. Out-of-bounds or masked samples return no observation. A global duplicate seam uses one canonical longitude. This coordinate contract is covered by [terrain processing](../test_terrain_processing.py), [coordinate conversion](../test_route_planner.py) and [boundary regressions](../tests/test_sprint_validation.py).

## Slope estimation

Point slopes use central axial differences at the containing pixel's centre. The centre and its four north/south/east/west neighbors must be valid. Diagonal pixels are not used. Unsupported dataset edges or missing required samples yield an unavailable slope.

For valid elevations, the method is:

```text
gx = (z_east − z_west) / (2 × dx)
gy = (z_south − z_north) / (2 × dy)
slope_degrees = degrees(atan(sqrt(gx² + gy²)))
```

For a geographic raster with reference axes `a` and `b`:

```text
R = (2a + b) / 3
dx = R × radians(pixel_longitude_width) × abs(cos(pixel_centre_latitude))
dy = R × radians(pixel_latitude_height)
```

For supported projected input, the inverse equidistant-cylindrical transform supplies angular spacing before applying the same spherical surface-spacing model. This is a disclosed approximation, not exact ellipsoidal terrain geometry. The native PDS products use planetocentric latitude; the derivative's horizontal ellipsoid tag alone does not prove a geodetic conversion. At effectively degenerate east–west spacing (`dx ≤ 0.001 m`), slope is unavailable.

[terrain_region.py](../terrain_region.py) reads a one-native-pixel halo around each regional window. It calculates slopes using that support and then crops to the displayed grid. This makes interior regional slopes use the same stencil as point slopes. A halo outside the actual dataset stays masked.

The shared array classifier uses central differences internally and one-sided differences at its array edges; a regional display's edge uses the surrounding halo rather than substituting a one-sided native derivative. Global slopes are calculated from the averaged global grid, with wrapped longitude neighbors and supported latitude-edge differences.

## Illustrative terrain classes

| Class | Estimated slope | Routing multiplier | Interpretation |
| --- | --- | ---: | --- |
| LOW | Up to 5° | 1 | Lower slope in this DEM-scale screening model |
| MODERATE | Above 5° to 15° | 3 | Increased illustrative traversal cost |
| HIGH | Above 15° to 25° | 8 | Larger illustrative traversal cost |
| EXTREME | Above 25° | 20 | Finite penalty; still traversable in this model |
| NO DATA | Missing centre/support or invalid class | Blocked | Unavailable evidence, not safe terrain |

These thresholds are retained project assumptions, not certified astronaut or rover safety limits. The array classifier rounds slope to 12 decimal places before inclusive threshold comparison to avoid floating-point boundary artifacts. The point API reports slope to three decimals and chooses its label from the unrounded point estimate; rounded display values should not be used to reconstruct a boundary decision.

## Regional and global analysis

A default regional request covers a nominal 0.5° × 0.5° window around its centre, clipped to actual dataset coverage. Dimensions follow raster spacing, rather than a fixed pixel count. For the recorded 128 samples/degree equatorial sample, this yields 64 × 64 cells. Each row uses its own latitude-dependent east–west spacing.

For global planning, [global_navigation.py](../global_navigation.py) warps elevations by coordinates onto a canonical 360 × 180 grid of 1° cells using average resampling. A bounded half-native-pixel registration envelope permits the recorded derivative's small edge discrepancy without stretching its pixels. A valid coarse average can exclude masked native samples, so it does not prove that all underlying native terrain is observed. Coarse slope classes lose smaller features.

Route distances use great-circle segments on a 3,389.5 km sphere, independent of the CRS-derived mean radius used for slope spacing. The difference is explicit; neither model includes terrain-following vertical travel, soil mechanics or vehicle dynamics. See [routing algorithms](ROUTING_ALGORITHMS.md).

## Validation and uncertainty

The [historical validation report](SCIENTIFIC_VALIDATION.md) distinguishes real sample tests, public-reference comparisons, controlled missing-data regressions, browser interactions and the owner's later full-DEM smoke checks. A match to another MOLA-derived product establishes numerical consistency under a method, not independent observational accuracy. Passing software checks do not calibrate slope classes to a rover or astronaut.

Reproduce available checks using [VALIDATION.md](VALIDATION.md), with each input's hash, product identity, environment, commands and skips retained. Preserve missing results and uncertainty beside successful cases. The practical implications are collected in [LIMITATIONS.md](LIMITATIONS.md).
