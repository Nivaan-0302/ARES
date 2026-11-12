# Changed-files report

Comparison base: the original uploaded `ARES_Source.zip`, SHA256 `445290aebeda1c1da70b33ac363f471e7a2d81c8db829f118847db3778fbc7d2`. This inventory includes earlier retained fixes and the master-directive sprint. It is not a list of changes silently applied to the user's local computer.

**90 modified or added delivered files.** No original application source file is deleted. OS `.DS_Store` metadata and empty backup directories are omitted from release packaging without deleting anything in the original upload or working copies. The complete source ZIP contains new binary vendor assets that are also represented in the binary-capable patch.

| Status | File | Purpose |
| --- | --- | --- |
| Added | `ASSET_PROVENANCE.md` | Asset/source/rights register with explicit unresolved origin and licensing. |
| Added | `DEPLOYMENT.md` | Actual Flask/WSGI requirements, storage/security/readiness and deployment checklist. |
| Modified | `README.md` | Current setup, actual results, methods, authorship and remaining limits. |
| Added | `REPAIR_STATUS.md` | Preserved prior-stage repair record clearly marked historical. |
| Added | `THIRD_PARTY_NOTICES.md` | Original licenses and versions for vendored dependencies. |
| Added | `collect_dem_metadata.py` | Read-only original-raster metadata/checksum collector. |
| Added | `dem_data.py` | Shared validated raster geometry, units/masks, slope stencil and read-only metadata cache. |
| Added | `docs/ASSET_INVESTIGATION.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/BUG_FIXES.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/CHANGED_FILES.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/COMPETITION_READINESS.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/DATASET_PROVENANCE.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/DEPENDENCIES.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/PERFORMANCE.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/SCIENTIFIC_INPUTS.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/SCIENTIFIC_VALIDATION.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/SPRINT_REPORT.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/SUBMISSION_GUIDE.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/VALIDATION.md` | Implementation, scientific, provenance, competition or reproducibility report. |
| Added | `docs/evidence/additional_tests.log` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/dependencies.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/dependency_check.log` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/derivative_transform_hypothesis.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/endpoint_performance.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/final_verification.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/frontend_node.log` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/global_reference_metadata.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/global_reference_results.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/native_pds_comparison.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/owner_dem_metadata.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/real_backend_browser.log` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/root_tests.log` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/source_access.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/synthetic_browser.log` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/usgs_sample_comparison.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `docs/evidence/usgs_source_header.json` | Recorded, scoped validation/research/software/performance evidence. |
| Added | `geo_rules.py` | Dependency-free shared longitude and half-open pixel-area conventions. |
| Modified | `global_navigation.py` | Coordinate-aligned coarse global model, cached data, wrapped A* and conservative shortcuts. |
| Modified | `globe.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Added | `globe_bootstrap.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Modified | `index.html` | Frontend asset loading, form feedback, accessible controls and scientific labels. |
| Modified | `mission_brief.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Modified | `mission_control.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Added | `mission_geometry.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Modified | `mission_routing.py` | Shared mission selection, precise metrics and truthful/sanitized scientific reports. |
| Added | `mission_service.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Modified | `mission_state.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Modified | `orbital_workspace.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Modified | `phase5_comparison.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Modified | `phase5_comparison.py` | Same-grid distance-only Dijkstra and terrain-weighted A* with consistent geometry. |
| Modified | `public_polish.css` | Preserved interface styling with focused responsive/accessibility improvements. |
| Modified | `public_polish.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Added | `requirements-browser.txt` | Runtime/production/browser dependency declaration or exact tested pins. |
| Added | `requirements-production.txt` | Runtime/production/browser dependency declaration or exact tested pins. |
| Added | `requirements-tested.txt` | Runtime/production/browser dependency declaration or exact tested pins. |
| Added | `requirements.txt` | Runtime/production/browser dependency declaration or exact tested pins. |
| Modified | `route_planner.py` | Physical-distance regional A*, exact classes/centres and consistent boundary conversion. |
| Modified | `route_refinement.py` | Geodesic sparse refinement, exact NoData policy, truthful counters and one profile. |
| Modified | `script.js` | Frontend mission/data/rendering/state/accessibility integration or regression fix. |
| Added | `scripts/compare_pds_reference.py` | Bounded reference preparation/comparison or local profiling utility. |
| Added | `scripts/compare_usgs_window.py` | Bounded reference preparation/comparison or local profiling utility. |
| Added | `scripts/prepare_global_reference.py` | Bounded reference preparation/comparison or local profiling utility. |
| Added | `scripts/profile_endpoints.py` | Bounded reference preparation/comparison or local profiling utility. |
| Modified | `terrain_api.py` | Restricted assets, validated API contracts/errors, dataset status, concurrency and readiness. |
| Modified | `terrain_region.py` | Clipped native region, derivative-support halo and latitude-dependent spacing. |
| Modified | `test_global_navigation.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Modified | `test_hazard_avoidance.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Modified | `test_mission_routing.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Modified | `test_route_planner.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Modified | `test_route_refinement.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Added | `test_terrain_processing.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Modified | `test_terrain_region.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Added | `tests/frontend_browser_smoke.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Added | `tests/frontend_real_backend.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Added | `tests/frontend_regressions.cjs` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Added | `tests/test_api_contract.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Added | `tests/test_cross_module_regressions.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Added | `tests/test_sprint_validation.py` | Regression, real-data or browser test; fixtures are explicitly separated. |
| Added | `vendor/SHA256SUMS` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/leaflet-1.9.4/LICENSE` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/leaflet-1.9.4/images/layers-2x.png` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/leaflet-1.9.4/images/layers.png` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/leaflet-1.9.4/images/marker-icon-2x.png` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/leaflet-1.9.4/images/marker-icon.png` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/leaflet-1.9.4/images/marker-shadow.png` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/leaflet-1.9.4/leaflet.css` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/leaflet-1.9.4/leaflet.js` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/three-0.160.1/LICENSE` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/three-0.160.1/build/three.module.js` | Pinned offline frontend dependency or original upstream notice/checksum. |
| Added | `vendor/three-0.160.1/examples/jsm/controls/OrbitControls.js` | Pinned offline frontend dependency or original upstream notice/checksum. |

Protected original files `AGENTS.md`, `AUTHORS.md`, `COPYRIGHT`, `DEVELOPMENT_HISTORY.md` and `mars_hero.png` remain byte-identical. No project LICENSE was added, image replaced, original DEM redistributed, Git commit created, or application published/deployed.
