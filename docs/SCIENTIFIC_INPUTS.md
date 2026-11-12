# Scientific inputs and evidence levels

## Owner's original full derivative

The full2.12 GB file was not available in this environment. The owner supplied Rasterio metadata, reproduced in [owner metadata](evidence/owner_dem_metadata.json):46,081 × 23,041 Int16, ESRI:104905, NoData −32768, scale 1 / offset 0, PixelIsArea, origin −180° / 90°, spacing 0.00781224569558698°. Reported bounds are west −180°, east 179.99609389834364°, south −90.0019530720196°, north 90°.

Those are owner-reported full-file facts, not an independent read of that file. They explain why exact-world-edge validation was incorrect: the derivative is short of the eastern meridian by roughly half a pixel and extends south by roughly a quarter pixel. The new bounded registration check and coordinate-aligned coarse warp accommodate that geometry without stretching or overwriting native data.

## Independently available sample and references

The uploaded `mola_sample_256.tif` was actually read with Rasterio/GDAL. Its dimensions, transform, CRS, NoData and all 65,536 values were checked. SHA256:

`c99f92579062c39934295690bd0a0644d3e73a60a1c7fbf14c93d714d6198981`

The sample contains no NoData cells and has no encoded band unit. It validates equatorial numerical behavior, not native missing-data occurrence or polar accuracy. Controlled Rasterio MemoryFile fixtures test missing-data and edge behavior explicitly.

Native PDS labels establish meter-valued radius-minus-areoid topography and planetocentric latitude for those products. A bounded window of a public projected USGS COG, virtually warped to the sample grid, exactly reproduces the sample. See [provenance](DATASET_PROVENANCE.md) for exact URLs, registration, areoid-documentation distinctions and unresolved transformation history. Neither matching pixels nor the horizontal ESRI CRS proves the full owner's file history or its precise vertical reference.

A separate native 4 ppd global PDS reference was converted to temporary GeoTIFF without resampling for global integration tests. It is not substituted for the owner's dataset in production configuration or bundled with this source package.

## Runtime geometry and missing-data contract

- Supported input: north-up, axis-aligned Mars geographic degree grids or spherical Mars equidistant-cylindrical meter grids. CRS geometry, extent, finite scale/offset and units are checked. Unknown unit metadata is disclosed; unsupported units/CRS are rejected.
- Point and regional slope use the native pixel centre plus four axial neighbors, with the same masks and per-row spacing. A regional halo supplies valid outside-window neighbors; absent support at a true dataset boundary stays unknown. Diagonal neighbors not used by the derivative do not invalidate unrelated slopes.
- Cropped pixel areas are west/north inclusive, east/south exclusive. Equivalent longitudes align with a window; uncovered slivers are never snapped into the last cell. Global duplicate seam samples use one canonical meridian. Exact poles use adjoining global coarse latitude bands as a disclosed spherical convention, not invented native elevation.
- Unknown, fractional, nonfinite or undeclared hazard codes are not traversable. Unknown side cells block diagonal corner cutting. EXTREME is an explicit finite penalty, not a hard rover limit.
- Global means are a 1° aggregate. Masked native values can be excluded from a mean, so coarse availability does not certify continuous native coverage. Unknown coarse cells are blocked, and a conservative wrapped-cell cover guards short direct-corridor shortcuts. This model does not assert that every underlying native pixel was surveyed.

## Still needed for stronger scientific claims

1. Full local raster hash, original acquisition URL and processing record, including any reprojection/resampling/registration changes.
2. Confirmation of the derivative's latitude interpretation and vertical areoid/datum against its actual source history. Do not substitute a geodetic ellipsoid merely because it appears in a geographic CRS label.
3. Independent terrain/observational controls with stated tolerances; a derivative-to-source comparison is not independent measurement truth.
4. Threshold/cost sensitivity and vehicle-specific mobility calibration before making physical traversability claims.
5. Full original-DEM integration/performance tests and selected real regional/global traverses; the reference tests do not establish those missing results.

Collect full input metadata read-only with `python collect_dem_metadata.py /path/to/original.tif --sha256`. Keep the original unchanged. Never infer an overall scientific accuracy percentage from pixel-lookup agreement or floating-point residuals.
