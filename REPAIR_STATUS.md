> Historical record of the earlier corrected copy. Current implementation and real-dependency results are in [docs/SPRINT_REPORT.md](docs/SPRINT_REPORT.md). Statements below about unavailable packages or unexecuted integration describe that earlier stage.

# Implemented repairs and outstanding inputs

This source copy preserves the original ARES interface, regional/global routing,
refinement, dashboards, attribution and original source archive. No original DEM
was supplied or changed. No packages were installed, deployment performed, or
project license selected during preparation.

## Implemented

- Valid elevation and derivative-support masks; clipped regional bounds;
  per-row spacing; polar derivative masks; scaled/masked raster reads.
- Configurable DEM path, Mars geometry/unit checks, geographic and spherical
  equidistant-cylindrical support, global coverage checks and dateline wrapping.
- Full-precision route validation, exact endpoints, same-cell routing, spherical
  profile/refinement interpolation, truthful inspection counters and one final
  mission profile.
- Restricted public assets, source/data/dotfile denial, finite-coordinate
  validation before terrain work, bounded concurrent analysis, liveness and
  full-application dataset readiness endpoints.
- Correct globe texture coordinates; routing independent of WebGL; 2D fallback;
  shared regional requests; cancellation; stale-state resets; shared hazard
  controls; geodesic antimeridian seams; GPU cleanup and hidden-render suspension.
- Vendored pinned Leaflet/Three.js assets and their original notices.
- Dependency manifests, deployment instructions, isolated tests, scientific input
  collector, explicit methodology assumptions and submission preparation records.

## Checks actually executed

These results describe the preparation environment, not the user's real DEM.

| Check | Result and limits |
| --- | --- |
| Python syntax | 25 Python files parsed before final documentation edits |
| Coordinate and terrain processing suites | 16 cases: 13 passed, 3 skipped (2 absent-DEM checks and 1 absent-Rasterio check) |
| Additional Python regressions | 15 cases: 4 passed, 11 Flask/Rasterio API tests explicitly skipped |
| Original A* validation script | All three synthetic cases passed |
| Synthetic hazard avoidance case | Passed |
| Mission/refinement synthetic tests | 22 cases passed using an explicitly isolated Rasterio import adapter that blocks unexpected DEM access; not real Rasterio integration |
| Node frontend regressions | 6 cases passed |
| Chromium browser fixture | Normal renderer and forced-WebGL-failure scenarios passed with explicitly synthetic APIs; not Flask or MOLA integration |
| Vendor assets | 11 asset hashes checked; CSS references resolved; vendor JavaScript parsed |

Flask, Rasterio and Gunicorn are absent from this preparation interpreter. The
declared dependency ranges and actual Flask/Rasterio integration still need a
run in the intended installed environment. The full test commands and browser
fixture prerequisites are in `docs/VALIDATION.md`. Skipped checks did not pass.

## Outstanding items requiring evidence or owner decisions

- The owner reports a roughly 2.12 GB Int16 raster, 46,081 by 23,041 pixels,
  ESRI:104905, named `mola128_mola64_merge_90Nto90S_SimpleC_clon0.tif`.
  The raster was not inspected here; original source and processing history
  remain unverified. Do not assume it was unmodified.
- Supply the raster or an accessible authoritative download, metadata packet,
  product label/citation, vertical reference, preprocessing history and any
  independent reference observations to complete real-data scientific work.
- Hazard thresholds/costs remain disclosed application heuristics. Calibration,
  sensitivity measurements, real-data performance and rover-specific safety
  validation have not been fabricated.
- The owner explicitly leaves licensing undecided. No LICENSE was added.
- The creator, source, usage rights and AI-generation status of `mars_hero.png`
  remain unknown. It has not been attributed to NASA or an AI generator.
- Official event/resource links are documented. The selected challenge and
  applicable rules still require confirmation; no competition eligibility is
  asserted.

Do not describe this package as every issue scientifically resolved or as a
flight-qualified or rover-safe navigation system. The implementation repairs are
provided for the next real-data run with the required inputs.
