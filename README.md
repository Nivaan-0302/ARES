# ARES — Mars Terrain Intelligence & Mission Planning

**Creator and Project Lead:** Nivaan Raina  
**Copyright:** © 2026 Nivaan Raina  
**Project:** NASA Space Apps Challenge 2026  
**Status:** Research and educational prototype with executed real-sample and public-reference validation

ARES combines a Mars globe and map, native DEM elevation/slope sampling, regional hazard grids, terrain-weighted A*, coarse global navigation, sparse local refinement, route comparisons, elevation profiles, dashboards, and deterministic mission briefs. Its output is a terrain-planning research aid, not a rover-certified traverse.

## Install and run

Python 3.12 is the tested target. Install into an isolated environment:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-tested.txt
export ARES_DEM_PATH='/absolute/path/to/your/authorized/mola-dem.tif'
python terrain_api.py
```

Open `http://127.0.0.1:5001`. The default dataset path, if the environment variable is absent, is `data/mola128_mola64_merge_90Nto90S_SimpleC_clon0.tif`. Keep the original raster unchanged and outside publicly served assets. The DEM and isolated environment are not bundled with this source package.

`requirements.txt` contains runtime compatibility ranges. `requirements-production.txt` adds optional Gunicorn. `requirements-tested.txt` pins the exact runtime/production environment exercised in this sprint; `requirements-browser.txt` adds the recorded browser-test packages. System-wide Python was not modified. See [dependencies](docs/DEPENDENCIES.md) and [deployment](DEPLOYMENT.md).

The interface can load without a DEM. `/healthz` checks process liveness. `/readyz` checks dataset compatibility and global coverage; a partial sample intentionally returns503 with regional capability available and global capability unavailable. This is not a scientific-accuracy certificate. Missing terrain and dataset failures produce explicit error states, never simulated observations.


**Mars hero image:** NASA/JPL-Caltech, Viking Orbiter mosaic. Source: [NASA Science — Mars Planet Globe](https://science.nasa.gov/resource/mars-planet-globe/). Resized to 600 × 600 pixels and converted from JPEG to PNG. NASA does not endorse ARES.

## What was validated

The implementation sprint executed **72 named Python tests: 70 passed, 2 full-original-DEM tests skipped**. Eight Node regressions and two real-backend browser scenarios passed, alongside two explicitly synthetic browser scenarios. Rasterio/Flask were actually installed and exercised; these sprint results do not rely on the previous import adapters.

All 65,536 pixel-centre lookups matched the provided real 256 × 256 sample. A nearest-neighbor virtual warp of a bounded window from the closest public USGS COG reproduced all 65,536 sample values exactly. This identifies a strong source candidate for the tested window; it does not prove the entire local file's identity or scientific ground truth. A separate, pixel-preserving2 MB native PDS 4 ppd reference exercised real global routing without downloading a multi-gigabyte DEM.

See [the sprint report](docs/SPRINT_REPORT.md), [scientific validation](docs/SCIENTIFIC_VALIDATION.md), [dataset provenance](docs/DATASET_PROVENANCE.md), [bug fixes](docs/BUG_FIXES.md), and [reproduction commands](docs/VALIDATION.md). Passing cases, skipped cases, unavailable evidence, source comparisons, and model limitations are separated explicitly.

## Scientific methods and limits

- Native samples honor valid-data masks, NoData, scale and offset. Known non-meter elevation units are rejected; absent unit metadata is explicitly flagged as an assumption. Gridded MOLA products can contain interpolated values rather than a direct laser observation at every cell.
- Point and regional slopes use central axial differences at native pixel centres, requiring the centre plus four axial neighbors. Regions read a one-pixel support halo. Missing support stays unavailable. Native/routing grid coverage is west/north inclusive and east/south exclusive. Equivalent longitudes are normalized without inventing coverage in cropped rasters.
- Physical slope spacing uses a documented spherical or mean-radius approximation with per-row cosine spacing. Routing distances use a 3389.5 km sphere. Native PDS documentation states planetocentric latitude; the horizontal CRS alone does not establish a planetographic conversion or vertical datum. See the provenance report before interpreting model differences.
- LOW ≤5°, MODERATE >5° to 15°, HIGH >15° to 25°, EXTREME >25° are chosen DEM-scale categories. Class costs 1, 3, 8, 20 are illustrative penalties. EXTREME remains traversable at high cost; unknown classes/cells and blocked diagonal corners are unavailable.
- Regional grids are derived from the actual raster spacing; the supplied128ppd sample yields64 × 64 cells for the default 0.5° window. This size is not hard-coded for arbitrary input rasters.
- The 360 × 180 global model averages elevations onto a coordinate-aligned 1° grid. Registered half-native-pixel extent differences are bounded explicitly. Coarse means may exclude masked native samples; a valid coarse mean does not prove all underlying native cells are known. Unknown coarse cells are blocked. Smaller hazards, narrow gaps and native coverage are not continuously validated.
- Refinement inspects at most eight selected local windows. Attempted, sampled, skipped, unavailable and modified counts are separate. The coarse risk index is not recomputed into a continuous high-resolution risk assessment.
- Distance-only Dijkstra and terrain-weighted A* comparisons use the same regional grid and endpoints. Their costs are not measured energy, travel time, or rover failure probability. Risk is a class-count heuristic; route efficiency is geometric length relative to a great-circle reference.
- No model of wheel-scale rocks, soil strength, slippage, rover geometry, illumination, thermal constraints, dust, communications or mission operations is supplied. No operational safety, global accuracy percentage, competition eligibility, or award is claimed.

## Authorship, AI assistance and rights

ARES is independently directed by **Nivaan Raina**, its creator and project lead. Preserve `AUTHORS.md`, `COPYRIGHT`, `DEVELOPMENT_HISTORY.md`, and `AGENTS.md`.

ChatGPT assisted with implementation, debugging, technical audit, scientific numerical analysis, testing, documentation and interface work. Routes are calculated by explicit terrain algorithms, not generated by a conversational AI model. Maintain accurate assistance disclosures and distinguish project leadership from algorithmic validation.


Original ARES software and documentation are distributed under the MIT License. See [LICENSE](LICENSE) for the full terms. Copyright © 2026 Nivaan Raina. NASA datasets, external imagery, vendored libraries, and other third-party assets retain their applicable rights and licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [ASSET_PROVENANCE.md](ASSET_PROVENANCE.md). The origin and reuse rights of `mars_hero.png` remain unresolved; see [asset investigation](docs/ASSET_INVESTIGATION.md). ChatGPT's material development assistance is disclosed above.


The selected Space Apps challenge remains unconfirmed. [Competition readiness](docs/COMPETITION_READINESS.md) distinguishes verified implementation, indexed official evidence, blocked live sources, and missing submission decisions.
