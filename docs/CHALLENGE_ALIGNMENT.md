# Challenge alignment: Martian Map

**Selected challenge:** [Interplanetary Survival Guide: Martian Map](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/)

**Project:** ARES — Autonomous Reconnaissance and Exploration System

**Creator and Project Lead:** Nivaan Raina

## What has been verified

The owner identifies this as the selected challenge. An official-domain indexed result independently confirms its title and URL. Direct retrieval of the complete official brief failed (HTTP 503; independent reader 502). A readable [Sonoma State institutional event page](https://edeon.sonoma.edu/nasaspaceapps-26/) reproduces the challenge overview; a Birla Institute local-event index corroborates it. The working objective below is a paraphrase of that institutional overview, not a claim that all official requirements, resources or submission conditions were verified. See [source-access evidence](evidence/challenge_source_review.json).

**Working objective:** combine multiple NASA mission datasets into a layered view of a Mars location or route that can help a human explorer plan surface activities and conduct science. The reproduced overview places this in the context of route/destination details and changing surface conditions. [NASA's event background](https://science.nasa.gov/universe/nasa-welcomes-all-ages-experience-levels-for-space-apps-challenge/) independently discusses Martian surface activity and integration across Mars missions. It does not supply a detailed checklist for this challenge.

ARES addresses a bounded part of that problem: **understanding DEM-scale terrain and comparing modeled routes before interpreting their limits**. It does not establish that a person or rover can safely traverse the displayed path.

## Capability-to-evidence matrix

“Demonstrated” below means implemented and supported by the linked software/evidence. “Partial” describes a contribution toward the reproduced overview. It is not a formal compliance judgment against the unavailable full brief.

| Challenge-relevant activity | ARES contribution and status | Implementation | Supporting evidence and limit |
| --- | --- | --- | --- |
| Explore a Mars location | **Demonstrated:** coordinate entry, interactive 3D globe and 2D map share start/destination state | [index.html](../index.html), [mission_state.js](../mission_state.js), [globe.js](../globe.js), [script.js](../script.js) | [Frontend regressions](../tests/frontend_regressions.cjs) cover coordinate geometry and stale-request behavior; [real-backend browser checks](../tests/frontend_real_backend.py) exercise rendering/fallback interactions |
| Interpret topographic terrain | **Demonstrated:** raster elevation, central-axial slopes and regional hazard grids | [dem_data.py](../dem_data.py), [terrain_region.py](../terrain_region.py) | [Terrain processing tests](../test_terrain_processing.py), [scientific validation](SCIENTIFIC_VALIDATION.md); derived slopes are estimates, not direct obstacle observations |
| Investigate a modeled route | **Demonstrated:** terrain-weighted regional A* and coarse global routing with bounded local refinement | [route_planner.py](../route_planner.py), [mission_routing.py](../mission_routing.py), [global_navigation.py](../global_navigation.py), [route_refinement.py](../route_refinement.py) | [Mission tests](../test_mission_routing.py), [global tests](../test_global_navigation.py), [refinement tests](../test_route_refinement.py); costs are illustrative and global refinement does not inspect every corridor cell |
| Compare route trade-offs | **Demonstrated:** distance-only Dijkstra and weighted A* use the same regional grid/endpoints | [phase5_comparison.py](../phase5_comparison.py), [phase5_comparison.js](../phase5_comparison.js) | [Cross-module regressions](../tests/test_cross_module_regressions.py); lower modeled cost is not lower measured energy, time or injury probability |
| Integrate NASA mission information | **Partial:** MGS/MOLA-derived topography drives analysis; external Viking MDIM21 imagery supplies map context; NASA/JPL-Caltech Viking image supplies a separately credited illustration | [script.js](../script.js), [asset provenance](../ASSET_PROVENANCE.md), [dataset provenance](DATASET_PROVENANCE.md) | [Public source comparison records](evidence/usgs_sample_comparison.json); imagery and DEM are separate products. This is not a calibrated multi-instrument science/environment fusion system; tile-service availability is external |
| Explain findings and uncertainty | **Demonstrated:** route metrics, sampled elevation profile, exposure counts, scientific report and deterministic Mission Decision Brief | [mission_service.js](../mission_service.js), [phase4_intelligence.js](../phase4_intelligence.js), [mission_brief.js](../mission_brief.js), [mission_routing.py](../mission_routing.py) | [Node checks](../tests/frontend_regressions.cjs), [browser checks](../tests/frontend_real_backend.py); summaries interpret algorithm outputs and introduce no new observations |
| Support science activities along a route | **Partial:** users can inspect topography, compare paths and discuss terrain hypotheses | Same terrain/report modules above | No implemented catalog of science targets, mineral detections, sample priorities or instrument task scheduling; no claimed new scientific discovery |
| Plan or execute an astronaut Marswalk | **Not implemented as a complete capability:** no suit/crew/EVA constraints or operational navigation system | Scope shown by existing input/API surface in [terrain_api.py](../terrain_api.py) | No verified astronaut-specific mobility, consumables, radiation, weather or rescue model; terrain routes are research outputs |
| Update current surface conditions | **Not implemented:** static raster analysis and optional imagery access | [dem_data.py](../dem_data.py), [script.js](../script.js) | External tile access is not live weather, radiation or surface telemetry |

## Scientific foundation

MOLA measured Mars with a laser altimeter on Mars Global Surveyor. ARES reads a local MOLA-derived raster through Rasterio, honors masks/NoData and scale/offset, and estimates slopes using neighboring elevations and physical-spacing approximations. It screens LOW ≤5°, MODERATE >5° to 15°, HIGH >15° to 25° and EXTREME >25°. These thresholds and routing penalties are demonstration assumptions, not certified astronaut or rover limits. The [methodology](METHODOLOGY.md), [routing explanation](ROUTING_ALGORITHMS.md) and [limitations](LIMITATIONS.md) describe the implemented model.

The owner's 128-ppd-class derivative, historical regional sample and separately prepared native 4-ppd PDS reference are different inputs. Recorded comparisons help establish product consistency, not independent ground truth. A known original-file hash does not resolve every preprocessing or inherited vertical-reference question. See [validation](SCIENTIFIC_VALIDATION.md) and [provenance](DATASET_PROVENANCE.md).

## What is original about ARES

The contribution is the connected application workflow: choose points consistently on map/globe, inspect NASA-derived terrain, compare established search objectives, examine profiles/exposure and receive an explainable scope-aware brief. A* and Dijkstra are established algorithms, and NASA data remain credited to their missions/products. ARES does not claim to have invented those algorithms or datasets, to be the world's first, or to be NASA endorsed.

## Gaps and future work

These are project development options inferred from the overview and present limits, **not independently verified official requirements**:

1. Add independently sourced science-target/geologic layers with per-layer provenance, resolution, registration and uncertainty; test coordinate alignment before combining them.
2. Add genuinely distinct mission/instrument data where useful to a defined planning question. Keep static observations, calculated estimates and forecasts visibly separate.
3. Study thermal, illumination, radiation and dust context only with identified products, appropriate time/season coordinates and validation; no fabricated “live” layers.
4. Develop vehicle- or astronaut-specific mobility and EVA/consumables constraints with domain review and defensible calibration before making human-safety statements.
5. Evaluate the workflow with real users; retain actual feedback and reproducible task outcomes rather than invented impact metrics.
6. Verify the full official brief and local rules, then update the mapping for any requirements absent from the institutional overview.

## Presentation boundary

A defensible pitch is: **ARES turns NASA-derived topography into inspectable route trade-offs, while showing where terrain data alone cannot support a mission decision.** A terrain-planning aid can contribute to a broader Marswalk map without claiming to solve all astronaut survival constraints. Follow the [demo guide](SUBMISSION_GUIDE.md) and label each input/fixture shown.
