# Implemented bug fixes

12 November 2026. The tables distinguish historical defects from residual inconsistencies fixed this sprint.

## Retained corrections to the original archive

| Cause and affected files | Smallest implemented correction and evidence |
| --- | --- |
| Rounded distance validation rejected valid routes; same-cell endpoints detoured through the cell centre. `route_planner.py`, `mission_routing.py`, `phase5_comparison.py` | Preserve precision until formatting; directly join endpoints in one available cell. `test_mission_routing.py` covers the formerly rejected 0.3° route, exact endpoints and same-cell geometry. |
| Profile/refinement interpolation disagreed with spherical distances; missions sampled profiles twice. `route_refinement.py`, `mission_routing.py` | Share spherical interpolation and one final profile. `test_route_refinement.py` checks high-latitude midpoints and antipodes; mission tests assert one profile call. |
| Failed or skipped refinement windows increased reported inspection coverage. `route_refinement.py` | Separate attempted, sampled, skipped, unavailable and modified counts; retain coarse hazard scope. The mixed-status refinement regression verifies these counters. |
| Flask exposed project files; expensive requests lacked bounded admission; global tests permanently replaced the model. `terrain_api.py`, `test_global_navigation.py` | Allowlist assets, bound concurrency, keep health independent, and scope test patches. `tests/test_api_contract.py` covers private assets, busy responses and slot release. Dependency manifests/local libraries fix broken setup and CDN-only startup. |

## Master-sprint corrections

| Cause and affected files | Implemented behavior and targeted evidence |
| --- | --- |
| Grid/native edge rules, longitude equivalence and rounded centres disagreed. `geo_rules.py`, `dem_data.py`, `route_planner.py`, `global_navigation.py` | West/north-inclusive, east/south-exclusive coverage; whole-turn alignment; exact centres; equivalent ±180° global meridian. `tests/test_sprint_validation.py` checks edges/longitude and all 65,536 real-sample pixel-centre lookups. |
| Missing centres could appear LOW; point/regional derivative support differed. `dem_data.py`, `terrain_region.py`, `terrain_api.py` | Require centre plus four axial neighbours, pixel-centre spacing and a regional halo. Unavailable support stays unknown. Rasterio mask regressions verify five unavailable cells around one missing centre and point/region agreement. |
| Strict bounds rejected reported subpixel registration; resizing could shift the grid. `dem_data.py`, `global_navigation.py` | Bound the registration tolerance; use coordinate-aligned `WarpedVRT` averaging. Owner-extent acceptance, larger-gap rejection and fractional-overlap regressions passed. The absent full DEM remains unverified. |
| Repeated validation added overhead; integer casts made invalid hazard codes traversable. `dem_data.py` and routing/comparison modules | Cache copied metadata for open read-only handles; accept exact classes 0–3. Cache-mutation/malformed-code regressions passed; independent Dijkstra comparisons protect A* costs. |
| Fixed shortcut samples could skip unknown polar longitude cells. `global_navigation.py` | Conservatively screen wrapped intervening coarse cells and a halo before shortening a route. The polar missing-cell regression prevents that shortcut. Native-resolution continuous coverage remains unverified. |
| Dataset failures were confused with coordinate errors; optional-profile errors could expose local paths. Backend and routing modules | Return explicit unavailable-dataset 503 and outside-coverage 422 responses; retain optional-profile gaps and log private diagnostic details server-side. API and profile-error regressions passed. |
| Missing profile readings were joined visually; failures lacked reliable retry/loading feedback. Frontend service, geometry and interface files | Preserve profile gaps, expose retry/error state, reject stale results, and improve keyboard/mobile access. Eight Node checks and real-backend WebGL/fallback browser scenarios passed. |

## Evidence and limits

[Recorded verification](evidence/final_verification.json): **70 Python passes, 2 additional skips, zero failures**; eight Node checks; two controlled-API browser scenarios and two actual-backend scenarios. See [scientific validation](SCIENTIFIC_VALIDATION.md) for actual sample values, independent comparisons and evidence boundaries. This sprint used installed Flask/Rasterio; earlier dependency adapters are not real integration evidence.

The owner's full DEM, processing history and vertical-reference inheritance remain unverified. Coarse averaging conceals hazards; thresholds and terrain penalties are not rover mobility limits. Licensing, image provenance and challenge selection remain unresolved, not bugs declared solved here.
