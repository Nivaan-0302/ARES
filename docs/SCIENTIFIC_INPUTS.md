# Scientific inputs and evidence levels

ARES uses an externally configured elevation raster. The original full derivative, historical equatorial sample, public comparison products and controlled fixtures provide different kinds of evidence. Their results must remain separate. See [methodology](METHODOLOGY.md) for the implemented calculations and [validation commands](VALIDATION.md) for reproduction.

## Owner's original full derivative

The full 2.12 GB file is not present in this review workspace. The owner initially supplied Rasterio metadata, preserved in the [historical owner packet](evidence/owner_dem_metadata.json): 46,081 × 23,041 Int16, ESRI:104905, NoData −32768, scale 1 / offset 0, PixelIsArea, origin −180° / 90°, spacing 0.00781224569558698°. Reported bounds are west −180°, east 179.99609389834364°, south −90.0019530720196°, north 90°.

The later owner verification recorded a 2,123,874,317-byte file with SHA-256:

`c1ca69ee8fa552f126cdcf51644e31e0e1b56cf2968f1d0b2e20c89546daf793`

It also records two local regional integration passes: `test_terrain_region.RealTerrainRegionTests` and `test_route_planner.RealRoutePlannerTests`. See the [full-file provenance addendum](DATASET_PROVENANCE.md#local-full-file-integrity-verification--13-november-2026) and [validation addendum](SCIENTIFIC_VALIDATION.md#additional-full-resolution-dem-verification--13-november-2026). These are preserved owner records, not an independent execution against that raster in this workspace. The earlier packet's absent hash and the earlier sprint's skips remain accurate for their stages.

The geometry explains the bounded registration check: the derivative is short of the eastern meridian by roughly half a pixel and extends south by roughly a quarter pixel. The coordinate-aligned coarse warp accommodates that envelope without stretching or overwriting native data. A hash establishes file identity; it does not establish acquisition history, physical accuracy or complete valid coverage.

## Historical sample and public references

The supplied `mola_sample_256.tif` was read with Rasterio/GDAL during the recorded validation. Its dimensions, transform, CRS, NoData and all 65,536 values were checked. SHA-256:

`c99f92579062c39934295690bd0a0644d3e73a60a1c7fbf14c93d714d6198981`

The sample is absent from this review checkout. The historical numerical references in the tests are tied to that exact input; a different raster must not be relabeled as this sample. It contains no NoData cells and has no encoded band unit. Its results cover equatorial numerical behavior, not natural missing-data occurrence or polar accuracy. Controlled Rasterio MemoryFile fixtures exercise masks and edges separately.

| Input / comparison | Recorded result | What it establishes |
| --- | --- | --- |
| Historical 256 × 256 real sample | All 65,536 native pixel-centre lookups matched its raster values; independent surface-normal calculations checked interior slopes | Numerical consistency with the declared method for this input |
| Public projected USGS MOLA COG window | Nearest-neighbor virtual warp reproduced all 65,536 sample values exactly | Matching source-family window under that transform; not whole-file identity or unique processing history |
| Native PDS 128 ppd windows | 10,113 exact matches; MAE 3.3025970458984375, RMSE 5.166902762320328, maximum difference 84 | Product-consistency comparison under native pixel-area bin lookup; not independent accuracy |
| Separate PDS 4 ppd global reference | Global/dateline/high-latitude integration checks recorded against a pixel-preserving GeoTIFF conversion | Global pipeline behavior on this coarser identified reference |
| Synthetic rasters and grids | Controlled masks, scale/offset, coordinate edges, corner blocking and route/refinement cases | Behavior for constructed conditions, not observations of Mars |

Native PDS labels establish metre-valued radius-minus-areoid topography and planetocentric latitude for those products. Neither matching pixels nor the horizontal ESRI CRS proves the owner's precise vertical reference or transformation history. [Dataset provenance](DATASET_PROVENANCE.md) retains exact products, labels, URLs, registration and areoid-documentation distinctions. [Recorded evidence](SCIENTIFIC_VALIDATION.md) retains methods and scope; [submission readiness](SUBMISSION_READINESS.md) distinguishes checks performed during this review.

The 4 ppd reference is prepared separately using [the hash-verifying script](../scripts/prepare_global_reference.py). It is not bundled, silently substituted for the owner's original dataset, or an excuse to claim 128 ppd performance. The NASA Trek basemap is independent imagery and never supplies the terrain elevations used by these calculations.

## Runtime geometry and missing-data contract

- Supported input: north-up, axis-aligned Mars geographic degree grids or spherical Mars equidistant-cylindrical metre grids. CRS geometry, extent, finite scale/offset and units are checked. Unknown unit metadata is disclosed; unsupported units/CRS are rejected.
- Point and regional slope use the native pixel centre plus four axial neighbors, with the same masks and per-row spacing. A regional halo supplies valid outside-window neighbors; absent support at a true dataset boundary stays unknown. Diagonal neighbors not used by the derivative do not invalidate unrelated slopes.
- Cropped pixel areas are west/north inclusive, east/south exclusive. Equivalent longitudes align with a window; uncovered slivers are never snapped into the last cell. Global duplicate seam samples use one canonical meridian. Exact poles use adjoining global coarse latitude bands as a disclosed spherical convention, not invented native elevation.
- Unknown, fractional, nonfinite or undeclared hazard codes are not traversable. Unknown side cells block diagonal corner cutting. EXTREME is an explicit finite penalty, not a hard rover limit.
- Global means are a 1° aggregate. Masked native values can be excluded from a mean, so coarse availability does not certify continuous native coverage. Unknown coarse cells are blocked, and a conservative wrapped-cell cover guards short direct-corridor shortcuts.

## Still needed for stronger scientific claims

1. Original acquisition URL and processing record, including reprojection/resampling/registration changes; preserve the already recorded owner checksum.
2. Confirmation of the derivative's latitude interpretation and vertical areoid/datum against its actual source history. Do not substitute a geodetic ellipsoid merely because it appears in a geographic CRS label.
3. Independent terrain/observational controls with stated tolerances; a derivative-to-source comparison is not independent measurement truth.
4. Threshold/cost sensitivity and vehicle- or astronaut-specific mobility calibration before physical traversability claims.
5. Representative full-original-DEM global traverses, valid-coverage assessment, cold I/O, peak-memory and production-performance measurements. The two recorded regional smoke passes do not establish these broader results.

Collect input metadata read-only with `python collect_dem_metadata.py /path/to/original.tif --sha256`. Keep the original unchanged. Never infer an overall scientific accuracy percentage from pixel-lookup agreement or floating-point residuals.
