# Scientific validation

> **Historical evidence with a later owner addendum.** The original sprint results below remain unchanged. The subsequent full-resolution verification section records the owner’s file hash and two local regional integration passes; it does not replace the earlier run or establish a new full-DEM execution in this workspace. See [scientific inputs](SCIENTIFIC_INPUTS.md) for the current evidence map and [submission readiness](SUBMISSION_READINESS.md) for checks performed during this review.

Validation date: 12 November 2026. This report describes the completed local implementation sprint. It separates measured input values, calculated results, synthetic regressions, and remaining assumptions. ARES is a research and educational prototype; these results do not establish operational rover safety.

## Recorded verification outcome

The final recorded verification run passed **70 Python cases**, with **2 additional cases skipped** because the owner's full-resolution DEM was unavailable: 42 root cases comprised 40 passes and 2 skips; the additional suite passed all 30 cases. There were **zero failed cases** in that run. See [the recorded results](evidence/final_verification.json).

The same run completed eight Node frontend checks, two browser scenarios using controlled API fixtures, and two browser scenarios against the actual Flask/Rasterio backend and supplied sample. The real-backend scenarios covered normal WebGL operation and the 2D fallback when WebGL was unavailable. Browser checks isolated external NASA Trek imagery; they do not establish that the external basemap service was available. Python syntax checks covered 32 files, JavaScript syntax checks covered 17 files, and the dependency consistency check passed.

These were actual executions with the isolated Python 3.12.14 environment, Flask 3.1.3, NumPy 2.5.4, Rasterio 1.5.2, GDAL 3.12.2 and PROJ 9.8.1. Earlier read-only work used thin adapters where packages were unavailable; those earlier checks are not being presented as Rasterio or Flask integration tests. The sprint's named regression suites and real-data API tests used the actual installed dependencies. Version evidence is in [dependencies.json](evidence/dependencies.json).


## Additional full-resolution DEM verification — 13 November 2026

The project owner subsequently verified the original local MOLA-derived GeoTIFF:

- Dimensions: 46,081 × 23,041 pixels
- CRS: ESRI:104905
- File size: 2,123,874,317 bytes
- SHA-256: `c1ca69ee8fa552f126cdcf51644e31e0e1b56cf2968f1d0b2e20c89546daf793`

Two previously skipped real-DEM integration tests were executed locally using the original full-resolution raster:

1. `test_terrain_region.RealTerrainRegionTests` — passed.
2. `test_route_planner.RealRoutePlannerTests` — passed.

Result: 2 tests passed, 0 failures, 0 skipped, in 0.337 seconds.

These results verify the tested regional terrain-analysis and route-connectivity behaviors on the owner's actual dataset. They do not establish full-planet scientific accuracy, independent ground truth, or certified rover traversability.

The earlier sprint's test totals remain historical results from that separate execution environment.


## Supplied real sample

The supplied `mola_sample_256.tif` has SHA-256:

```text
c99f92579062c39934295690bd0a0644d3e73a60a1c7fbf14c93d714d6198981
```

The sample was read without modifying it. The actual-sample regression suite checks its hash after each test. Its measured properties are:

| Property | Result |
|---|---:|
| Dimensions | 256 × 256 pixels |
| Storage | One signed 16-bit elevation band |
| CRS | ESRI:104905, `GCS_Mars_2000` |
| Declared NoData | −32768 |
| Valid pixels | 65,536 |
| NoData pixels actually present | 0 |
| Minimum / maximum stored elevation | −1558 / −960 |
| Mean / median stored elevation | −1209.2385711669922 / −1193 |
| Longitude spacing | 0.00781224569558698° per pixel |
| Latitude spacing magnitude | 0.00781224569558698° per pixel |
| West / east pixel edges | −1.005826622711112° / 0.994108275359155° |
| South / north pixel edges | −0.9970378621971483° / 1.0028970358731186° |

The sample does not declare a vertical band unit. Rasterio reports the default scale 1 and offset 0; no separate elevation scale or offset is encoded. ARES explicitly reports `elevation_units_assumed: true` when interpreting these stored values as metres. Its horizontal CRS is not proof of its vertical datum. The source-family investigation supports metre units for authoritative MOLA topography, while the exact processing and vertical-reference inheritance of the owner's derivative remains unresolved.

Before the sprint environment was installed, independent decoding of the uncompressed signed TIFF strips matched native GDAL's decoded pixel array exactly. The decoded little-endian signed-int16 pixel array has SHA-256 `3b93731549f125fbaa396fd56c75ed34fe2174e62384f4b40a7aebcdc2e49269`. The final sprint subsequently exercised the sample through actual Rasterio reads.

## Coordinate and elevation validation

The real-sample test exhaustively checked lookup values at all **65,536 pixel centres** against the raster array. The coordinate `(latitude 0°, longitude 0°)` falls in zero-based **row 128, column 128**, whose centre is approximately `(−0.000976536010°, −0.001953050828°)`. Its measured stored elevation is **−1517**, reported as **−1517 m under the explicit metre assumption**.

Native and regional grid indexing use pixel-area boundaries: west and north edges are included; east and south edges are excluded. Equivalent longitude representations are aligned consistently; the global grid assigns +180° and −180° to the same meridian. Actual missing native coverage is not repaired by clamping an out-of-bounds point into an observed pixel.

The owner's reported full-raster metadata is **46,081 × 23,041**, west −180°, east 179.99609389834364°, north 90°, south −90.0019530720196°. These numbers were supplied by the owner; the full file was not available for independent inspection. The previous strict `1e-5°` global-extent test rejected this reported registration. The implementation now permits a bounded discrepancy of 0.51 native pixels per edge, capped at 0.01°, and resamples by geographic coordinates onto a canonical global grid. It does not stretch the native bounds to fit that grid. A synthetic offset-boundary step raster verifies the expected fractional overlap in the canonical cell. Larger extent gaps are rejected. Acceptance of this registration envelope establishes neither provenance nor complete valid coverage.

## Slope method and independent reference

For geographic input, the implemented screening model uses the CRS ellipsoid's mean radius:

```text
R = (2a + b) / 3
```

For this sample, `a = 3,396,190 m`, `b = 3,376,200 m`, and `R = 3,389,526.6666666665 m`. East–west spacing uses `R × angular_pixel_width × cos(pixel_centre_latitude)`; north–south spacing uses `R × angular_pixel_height`. At the equator, the sample spacing is approximately **462.159959 m** in this model. Each regional row uses its own pixel-centre latitude. This is an explicit spherical approximation, not an exact ellipsoidal geodetic calculation.

The independent numerical reference constructed 3D east–west and north–south secant vectors from adjacent measured elevations. Their cross product gives a local surface normal; the normal's angle from vertical gives slope. This geometric construction was compared with the production finite differences across all **64,516 interior sample cells**, using an absolute tolerance of **1e-10 degrees**. The real Rasterio regression passed, and its independently classified hazard array matched the production array.

| Interior-sample result | Current spherical screening model |
|---|---:|
| Minimum slope | 0° |
| Maximum slope | 7.836998693204767° |
| Mean slope | 0.9038457051986603° |
| LOW, slope ≤5° | 64,366 cells |
| MODERATE, 5° < slope ≤15° | 150 cells |
| HIGH, 15° < slope ≤25° | 0 cells |
| EXTREME, slope >25° | 0 cells |

The steepest interior sample cell is zero-based **row 128, column 100**, at approximately `(latitude −0.000976536010°, longitude −0.220695930305°)`, with stored elevation −1262. At `(0°,0°)`, the west/east samples are −1515/−1521 and north/south samples are −1512/−1523. The current pixel-centre reference slope is approximately **0.776646781498°**; the actual Flask API reports **0.777°**, classified **LOW**.

The original fixed-radius model, using 3,389,500 m, gives approximately 0.776652890967° at that pixel centre. The small numerical difference does not change any of the interior sample's four hazard classes. It should not be interpreted as a demonstrated improvement in physical accuracy.

### Latitude-convention sensitivity

Authoritative native MOLA documentation specifies **planetocentric** latitude. An ESRI ellipsoid label on the derivative does not establish that its pixel coordinates were converted to geodetic latitude. The sprint therefore does not silently replace the declared spherical screening model with ellipsoidal geodetic distances.

A conditional calculation treating the sample latitudes as geodetic on the tagged ellipsoid gives an interior maximum slope of **7.902126057474°**, with 64,365 LOW and 151 MODERATE cells. Three cells cross the 5° threshold between these models:

| Zero-based row, column | Spherical slope | Conditional geodetic slope |
|---|---:|---:|
| 22, 173 | 4.983978358° | 5.011369373° |
| 44, 230 | 5.008855439° | 4.999083135° |
| 129, 100 | 4.974237736° | 5.004087369° |

These are sensitivity results, not proof that the geodetic interpretation is the correct one or that the spherical implementation is a verified science error. Resolving the derivative's coordinate-processing history is still necessary. The near-equatorial sample also cannot validate high-latitude performance; polar spacing, missing-support and shortcut cases are covered by explicit synthetic regressions and a separate coarse global reference.

## Missing terrain and hazard policy

Native point and regional slope calculations now share the same measured support: a valid centre plus its four axial neighbours. A missing diagonal does not invalidate a derivative that does not use it. A missing centre or required axial neighbour makes the slope unavailable and the associated regional hazard cell `−1`; unknown cells cannot be traversed. This fixes the historical case where a missing centre elevation had a finite zero derivative and was incorrectly classified LOW.

Regional calculations read a one-native-pixel halo around the displayed window. Its supported edge cells therefore use the same central differences as point lookup. At a true dataset boundary, unavailable halo support stays masked. Clipped reads report the clipped window's bounds and dimensions. The global aggregate has its own coarse-grid edge derivatives; those require the samples used by their derivative and never substitute a missing source elevation with a valid zero.

Real Rasterio `MemoryFile` regressions cover NoData and internal masks, scale/offset application, actual dataset edges, central-difference support, halo behaviour, coordinate boundaries, malformed hazard codes and routing rejection of unknown terrain. The actual supplied tile contains no NoData; it cannot itself demonstrate correct behaviour on naturally missing terrain. That part of the evidence is explicitly synthetic. Regression checks also prevent fractional or nonfinite hazard codes from being truncated into valid traversable classes.

Thresholds 5°, 15° and 25° and traversal multipliers are heuristic demonstration choices. Their tests establish consistent implementation, not rover-specific mobility calibration. The risk score is a model-specific weighted index, not a probability of failure, energy estimate, travel-time estimate or guarantee of traversability.

## Actual regional API and browser result

With the supplied sample, the default region around `(0°,0°)` is **64 × 64** cells with bounds approximately west −0.255851036°, east 0.244132689°, north 0.252921449°, south −0.247062275°. Actual regional output contains **4,080 LOW**, **16 MODERATE**, no HIGH/EXTREME cells and no unknown cells.

The actual Flask `/api/mission-route` call from `(0°,0°)` to `(0.1°,0.1°)` returns:

| Result | Measured response |
|---|---:|
| Route distance | 8.667 km |
| Direct great-circle distance | 8.366 km |
| Returned polyline waypoints | 16 |
| Classified regional A* cells | 14, all LOW |
| Elevation-profile samples | 25 |
| Slope-profile samples | 25 |
| Sampled elevation range | −1517 to −1315, under metre assumption |
| Maximum sampled slope | 2.911538182773361° |

Grid cells, returned waypoints and profile positions have different roles; their counts are not interchangeable. The endpoints are preserved exactly. Risk index zero in this example reflects the fourteen LOW path cells; it does not establish an obstacle-free or rover-safe line. Profiles sample the returned route geometry, and gaps remain gaps rather than being rendered as measured values.

The real-backend browser test verified this route, profile rendering and map integration in normal WebGL and no-WebGL modes, subsequent out-of-coverage failure with a retry control, reset state, keyboard tab navigation and no horizontal overflow at a 390-pixel viewport. No terrain API response was mocked in those two scenarios. The sample correctly yields HTTP 503 for full-application readiness, with regional capability true and global capability false; its regional endpoints remain usable.

## Global routing evidence

A separately downloaded **4-pixels-per-degree native PDS global reference**, converted to a GeoTIFF without resampling, exercised the actual global Rasterio model and Flask routes. This is a lower-resolution reference, not the owner's unavailable full-resolution derivative. Its model contains 64,771 LOW and 29 MODERATE cells, with no HIGH, EXTREME or unknown cells in this reference run.

| Start → destination | Route / direct distance | Waypoints | API result |
|---|---:|---:|---|
| `(0°,179°)` → `(0°,−179°)` | 118.316 / 118.316 km | 2 | HTTP 200 |
| `(85°,170°)` → `(85°,−170°)` | 102.600 / 102.600 km | 2 | HTTP 200 |
| `(35°,10°)` → `(−35°,−170°)` | 10683.422 / 10648.428 km | 344 | HTTP 200 |

These outcomes exercise longitude wrapping, high latitudes and a long route. The global grid is **1°**, approximately 59 km north–south. Averaging elevation before estimating its slope removes smaller terrain features; the resulting LOW class is weak evidence about local exposure. Sampled refinement checks selected windows rather than continuously validating the complete corridor. A separate synthetic polar regression verifies that the direct-line shortcut does not skip unknown coarse cells.

The actual reference run measured approximately 0.0931 seconds for a cold coarse model and 0.000097 seconds for a cached model. Those measurements concern the small reference and local environment. They do not establish cold-load time, memory use or concurrent-service capacity for the approximately 2 GB owner raster. See [global reference results](evidence/global_reference_results.json) and the separate performance report for measurement scope.

## Comparison with authoritative elevation products

Two external comparisons used actual source bytes:

1. **Native PDS 128-pixels-per-degree topography.** Four bounded source ranges were compared by the native pixel-area bin containing each sample pixel centre. Of 65,536 pairs, 10,113 match exactly; mean absolute difference is **3.3025970458984375**, RMSE **5.166902762320328**, and maximum absolute difference **84** in the metre-valued topography scale. The central sample value is −1517 against native reference −1515. No fitted offset was applied. These are product-consistency differences, not an independent accuracy estimate or proof of a particular regridding history. See [native comparison evidence](evidence/native_pds_comparison.json).
2. **Closely matching USGS merged MOLA COG.** A bounded verified-HTTPS download of 737,280 bytes from the official source supported a nearest-neighbour virtual warp onto the supplied sample grid. **All 65,536 sample pixels matched exactly**, with zero MAE, RMSE and maximum difference. The source is projected ESRI:103885; the sample is geographic ESRI:104905. This strongly identifies a matching source family and local window. It does not identify the complete owner file's checksum, reproduce its processing history or supply independent observational ground truth. See [USGS comparison evidence](evidence/usgs_sample_comparison.json).

Authoritative source documentation establishes native MOLA topography as planetary radius minus an areoid, in metres, using planetocentric latitude and east-positive longitude. The source documentation describes the GMM3 (`mgm1025`) potential-model reference evaluated to degree/order 50; it must not be confused with the IAU 2000 coordinate reference. The derivative's exact provenance and vertical-reference inheritance still need confirmation. See the dataset provenance report for labels, source URLs and unresolved details.

## What remains unverified

- **Owner's full raster:** it was not supplied. Two corresponding tests were skipped. Whole-file checksums, complete spatial coverage, source lineage and full-resolution global numerical results remain unverified.
- **Observed NoData in the real sample:** there are no such pixels. Missing-data regressions use actual Rasterio with synthetic masked data.
- **Exact physical slope:** passing numerical reference checks validates the declared method, not ground-truth slope. Latitude convention, vertical reference, interpolation, original acquisition uncertainty and derivative history limit physical interpretation.
- **Rover-scale obstacles and mobility:** MOLA resolution cannot resolve individual rocks, sand traps or many local slopes; no rover-specific terrain, traction or environmental model was validated.
- **Continuous refined-route exposure:** regional checks are bounded and global refinement samples selected windows. Unknown or unsampled terrain must not be interpreted as a validated traverse.
- **Full-dataset performance and public deployment:** neither full-resolution cold-load performance nor production resource requirements were measured. No deployment or operational mission qualification was performed.
- **External basemap availability:** browser tests isolated those requests. Basemap imagery does not validate the elevation raster.

## Reproduction

Install the declared runtime requirements into an isolated virtual environment. Provide the unchanged real sample and, for global reference tests, separately prepare the documented PDS reference. The source package does not bundle the owner's DEM. Set `ARES_SAMPLE_PATH` and `ARES_GLOBAL_REFERENCE_PATH` to those inputs, then run the root test suite and additional tests with bytecode disabled:

```sh
GDAL_PAM_ENABLED=NO python -B -m unittest discover -s . -p 'test_*.py' -v
GDAL_PAM_ENABLED=NO python -B -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/frontend_regressions.cjs
```

`tests/test_sprint_validation.py` contains the actual-sample, real global-reference and synthetic metadata/NoData regressions. Tests requiring an unavailable external input explicitly skip; a successful command containing skips is not evidence that the skipped input was tested. The original full-raster tests additionally use `ARES_DEM_PATH`.

`scripts/compare_pds_reference.py`, `scripts/compare_usgs_window.py` and `scripts/prepare_global_reference.py` document the bounded scientific-reference procedures. Reference comparisons depend on external service availability. Configure the supplied sample as `ARES_DEM_PATH` for regional browser checks and run `tests/frontend_real_backend.py --url http://127.0.0.1:5001` against an already running local backend; those browser checks also require the optional browser dependencies and Chromium. Archived JSON results preserve what was actually observed in this sprint.
