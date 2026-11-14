# Submission and demonstration guide

**Creator and Project Lead:** Nivaan Raina · solo project

**Selected challenge:** [Interplanetary Survival Guide: Martian Map](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/)

This guide proposes a presentation structure. Required duration, slide count, submission fields, event-specific deadlines and eligibility have not been independently verified. The [alignment document](CHALLENGE_ALIGNMENT.md) separates the selected title, institutional overview and missing official brief. Prior Earth-analog candidate research remains in the explicitly historical portion of [competition readiness](COMPETITION_READINESS.md#historical-research-record--before-final-challenge-selection).

## One question for the demonstration

**How does DEM-scale terrain affect a modeled Mars route, and what can the available data actually tell us?**

Introduce ARES as the Autonomous Reconnaissance and Exploration System, created and independently directed by Nivaan Raina. Explain that its integrated map/globe, terrain analysis, established search algorithms and interpretable reports contribute the terrain-planning part of a layered Martian map. It is not a complete astronaut survival or operational navigation system.

## Prepare an honest application state

- Start the actual Flask application with an identified, authorized raster. Retain its product name, resolution, checksum and conversion method beside the demonstration.
- The original full owner raster, historical 256 × 256 sample and separate native 4 samples/degree public reference are different inputs. Use the [gallery](SCREENSHOT_GALLERY.md) and current [readiness record](SUBMISSION_READINESS.md) for the inputs actually available in this workspace.
- Use only coordinates inside the selected raster's valid coverage. Check `/healthz` and `/readyz`; a regional raster may support regional analysis while `/readyz` correctly reports global coverage unavailable.
- State whether external NASA Trek tiles loaded. Their imagery is separate from elevation calculations, and a blocked basemap is not proof that the DEM failed.
- Do not display recorded historical numbers as though they were a fresh execution. Keep synthetic fixtures explicitly labeled; do not present them as NASA observations.

## Suggested demonstration sequence

1. **Planetary Explorer.** Rotate the actual 3D globe, then switch to 2D. Explain whether the surface is DEM-derived color or a fallback visualization. Select Start and Destination, or enter coordinates explicitly.
2. **Terrain and hazards.** Show elevation, estimated slope and the regional grid. Describe LOW ≤5°, MODERATE >5° to 15°, HIGH >15° to 25° and EXTREME >25° as illustrative screening categories. Unknown terrain is unavailable; small boulders and wheel/foot-scale features are beyond coarse DEM evidence.
3. **Route Intelligence.** Show the actual calculated route length and waypoint/exposure counts. Explain that weighted A* trades distance against selected class penalties, while the great-circle line is only a geometric reference.
4. **Algorithm comparison.** Where regional data is available, compare distance-oriented Dijkstra with terrain-weighted A* on the same grid. Paths may be identical in low-relief terrain. Show the observed comparison without promising avoided hazards or a shorter path.
5. **Science Lab and Route Scientific Report.** Read the analysis scope, elevation profile and missing-data limits. Profile points sample a route; they do not measure continuous rover-safe or astronaut-safe clearance.
6. **Mission Decision Brief.** Show how deterministic rules explain route metrics and limitations. Material ChatGPT assistance in developing ARES is disclosed; the brief is not a conversational model inventing route observations.
7. **A truthful failure and closing scope.** If time permits, show a missing-data or invalid-coordinate response, then return to the valid state. End with the selected-challenge matrix, source credits, demonstrated integration and remaining multi-mission/environment/EVA gaps.

Keep the actual local format concise and accessible: readable units, captions, keyboard navigation and one clear decision question. Do not claim live mission telemetry, energy use, travel time, failure probability, NASA endorsement or certified traversability.

## Historical results available as supporting evidence

These measurements belong to prior recorded inputs/executions and are retained without relabeling them as current results:

| Recorded input | Supporting result | Scope |
| --- | --- | --- |
| Supplied 256 × 256 real MOLA-derived sample, [0°,0°] → [0.1°,0.1°] | 8.667 km, 16 waypoints, 25 valid profile samples in real-backend browser checks | Regional calculated route; external basemap isolated |
| Separate native public 4-ppd PDS reference, [0,179] → [0,−179] | 118.316 km | Global coarse-grid experiment with a distinct input |
| Supplied sample compared to a bounded USGS window | 65,536/65,536 values matched under documented nearest-neighbor virtual warp | Product/window consistency, not independent physical ground truth |
| Owner's full original DEM | Two regional integration tests subsequently recorded as passed | Owner's separate local execution; not a full-planet safety validation |

See [scientific validation](SCIENTIFIC_VALIDATION.md), [global reference results](evidence/global_reference_results.json), [USGS comparison](evidence/usgs_sample_comparison.json) and the [current check record](SUBMISSION_READINESS.md). Earlier real-backend checks exercised normal WebGL and no-WebGL fallback, 390 px mobile width, keyboard tabs and error recovery; those observations do not prove every device or external service works.

## Submission packet

- Verified final challenge/local-event instructions, required fields, time limit and deadline/time zone; preserve actual prior development dates and check their treatment under applicable rules.
- README and source, setup commands, tested dependencies, exact demonstration input identity and current verification outputs.
- Challenge-to-feature evidence matrix and understandable limitations; separate implemented features from future ideas.
- Genuine screenshots with input/fixture captions; pitch/video only in the confirmed event format.
- Dataset/product citations, derivative-processing uncertainties, NASA imagery credits, upstream notices and the [MIT License](../LICENSE) for original ARES material.
- Nivaan Raina's creator/project-lead attribution, accurate material AI-assistance disclosure and intact development history.

Do not fabricate user feedback, impact percentages, scientific accuracy, competition results or awards. Repository preparation does not itself register, publish, deploy or submit ARES.
