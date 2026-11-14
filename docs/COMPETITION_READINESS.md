# Competition readiness

**Selected challenge:** [Interplanetary Survival Guide: Martian Map](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/)

**Creator and Project Lead:** Nivaan Raina · independently directed solo project

## Current assessment

ARES demonstrates the terrain-intelligence portion of the selected challenge: a shared Mars map/globe, MOLA-derived elevation and slope analysis, modeled route planning, algorithm comparison, elevation profiles and deterministic decision briefs. The [challenge-alignment matrix](CHALLENGE_ALIGNMENT.md) links these capabilities to source and evidence. It also identifies missing environmental, science-target and human-exploration constraints. ARES is a research and educational prototype, not a complete astronaut survival planner.

The project owner selected this challenge in the final-submission directive. The official-domain search index independently confirms its title and URL. A fresh direct request returned HTTP 503 and the independent reader returned 502. A readable [Sonoma State local-event page](https://edeon.sonoma.edu/nasaspaceapps-26/) reproduces the overview; it supports a provisional summary, not a verified complete official requirement list. Source outcomes are recorded in [challenge_source_review.json](evidence/challenge_source_review.json). Registration, event-specific judging, deadlines, submission fields, development-period rules and eligibility remain unverified. Existing development history must be disclosed accurately; no timestamps have been shifted.

Current rights and evidence records supersede several open items in the historical assessment below:

- Original ARES software/documentation is MIT licensed; see [LICENSE](../LICENSE).
- The hero image is the documented NASA/JPL-Caltech Viking Orbiter replacement, separately credited in [asset provenance](../ASSET_PROVENANCE.md). This does not grant blanket rights to all third-party content or imply NASA endorsement.
- The owner recorded a later full-original-DEM hash/metadata check and two passing regional integration tests in [scientific validation](SCIENTIFIC_VALIDATION.md#additional-full-resolution-dem-verification--13-november-2026). That historical owner run does not establish new full-DEM execution in this workspace or full-planet ground truth.
- Earlier sample/reference and synthetic/browser records remain evidence of their own inputs and environments. Current execution and any screenshot inputs are reported separately in [submission readiness](SUBMISSION_READINESS.md).

| Judging consideration | Evidence to present | Remaining gap |
| --- | --- | --- |
| Scientific validity | Explicit finite-difference method, raster masks, numerical/reference comparisons, preserved input/result records | Derivative processing/vertical-reference uncertainty; no physical terrain or mobility ground truth |
| Technical execution | Regional A*, same-grid Dijkstra comparison, global 1° grid, bounded refinement, synchronized map/globe and error states | Representative full-DEM production load and external service availability |
| Creativity | One inspectable workflow connecting NASA terrain, route trade-offs, scope-aware reports and rule-based summaries | Standard algorithms and NASA datasets are credited, not claimed as inventions |
| Challenge relevance | Layered Mars terrain/route exploration, with imagery separate from elevation | Broader multi-mission science/environment integration and astronaut planning remain partial or absent |
| Presentation | Actual-interface gallery and a reproducible terrain-planning demonstration | Confirm local required format and time limit; collect real user feedback if available |

These considerations are an engineering review framework, not a verified scoring rubric for the owner's local event. No award, eligibility decision, NASA certification or operational safety claim is made.

## Submission completion gates

1. Obtain the complete selected challenge statement and local-event instructions from organizers; verify required fields, timing/time zone, rights and development-period rules against actual prior work.
2. Use the [demo guide](SUBMISSION_GUIDE.md), [alignment matrix](CHALLENGE_ALIGNMENT.md), and [limitations](LIMITATIONS.md) to keep the pitch tied to functioning terrain features.
3. Supply source citations, author/AI assistance disclosures, tested setup, input identities and the actual outputs shown. State which dataset and resolution drives each screenshot/demo.
4. Preserve documented owner verification while completing any required full-DEM/global/production checks on the authorized original input. Do not substitute a smaller reference for it silently.
5. Submit only through the owner's selected event workflow after its rules and third-party terms are checked. This repository work does not register, deploy or submit the project.

---

## Historical research record — before final challenge selection

The following assessment was prepared for the earlier investigation on 12 November 2026. Its statements about an unselected challenge, an Earth-analog candidate, unresolved licensing/image decisions and then-unavailable full-DEM tests describe that earlier stage. They are preserved as research history and are not the current selection or current rights status. The dated source-access results and actual reported measurements are unchanged.

# Earlier competition-readiness assessment

**Project:** ARES — Mars Terrain Intelligence & Mission Planning

**Creator and Project Lead:** Nivaan Raina

**Research access date:** 12 November 2026

ARES now has executed scientific, API, algorithm, and browser evidence. Competition alignment remains conditional: the owner has not selected a challenge, current official pages could not be read live, the original full DEM is unavailable here, and image rights and software distribution terms remain unresolved. No eligibility, award, or success claim is made.

## Official-source investigation and its limits

These are actual access outcomes, not assumptions that a URL is valid merely because it was supplied:

| Requested official source | Access outcome on 12 November 2026 |
| --- | --- |
| https://www.spaceappschallenge.org/ | Direct HTTPS 503, upstream connection failure |
| https://www.spaceappschallenge.org/2026/ | Direct HTTPS 503; independent web reader 502 |
| https://www.spaceappschallenge.org/2026/challenges/ | Direct HTTPS 503; independent web reader 502 |
| https://www.spaceappschallenge.org/legal/ | Direct HTTPS 503; independent web reader 502 |
| https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/ | Direct HTTPS 503; independent web reader 502 |

The response body reported an upstream connection failure, rather than providing challenge content. These results do not prove that the pages do not exist. A separate search service returned indexed text from the official event, candidate, legal, and local-event pages. Indexed content is useful provisional evidence; it is not confirmation of the current live rules or the owner's registration, event, team, deadline, or eligibility.

The indexed event page describes registration, team formation, and submission through a project's Team page. Confirm the current workflow and local-event deadlines directly before relying on them. Exact required pitch/video length, submission fields, judging weights, and applicable event-specific instructions were not verified.

The indexed legal page reports requirements to address an official challenge, cite sources, document third-party rights, and make original content unrestricted or OSI licensed. It also reports an Apache 2.0 default if no specific license is chosen. **Current live terms and their applicability were not verified.** The owner subsequently selected the MIT License for original ARES software and documentation; see ../LICENSE. Review the actual current submission terms and decide distribution rights before any submission, since leaving a local license undecided does not establish what an external submission agreement would do.

## Candidate challenge: conditional fit, not selection

The official-domain index identifies the candidate as **“Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars.”** Its indexed statement asks for identification and characterization of new terrestrial analogs using open Earth, Moon, and Mars data, presented through a map, visualization, or tool. This is broader than displaying Mars routes.

ARES contributes Mars topographic exploration, elevation/slope screening, route comparisons, and visualization. It currently has no Earth analog dataset, cross-body feature comparison, documented analog-selection method, uncertainty-aware similarity assessment, or demonstrated new terrestrial analog finding. If the owner selects this candidate, those are substantive relevance gaps. A Mars-only route demo cannot honestly be presented as completing the analog-identification task.

Because the full current challenge index was unavailable, this work cannot establish that this is the best challenge among all 2026 options. First select and record a challenge whose actual problem statement matches the intended contribution. If the analog candidate is chosen, scope a small, cited, reproducible comparative case study before adding functionality; do not add a broad Earth/Lunar platform merely to match a title.

## Evidence against a provisional judging framework

Indexed official 2026 local-event pages for [Ajmer](https://www.spaceappschallenge.org/2026/local-events/ajmer/) and [Faisalabad](https://www.spaceappschallenge.org/2026/local-events/faisalabad/) name Impact, Creativity, Validity, Relevance, and Presentation. They support using this planning framework. A current global rubric, scoring weights, and applicability to the owner's event were not independently retrieved.

| Criterion | Evidence ARES can show | Remaining meaningful gap |
| --- | --- | --- |
| Impact | A reproducible educational/research workflow showing how topography changes route choices | Identify a target user and document actual feedback or a measured decision benefit; no invented impact percentages |
| Creativity | Integrated map/globe, shared mission state, regional/global route scales, bounded refinement, interpretable reports | Explain the distinct contribution over existing tools and ordinary A*; use a concrete comparison rather than calling standard algorithms novel |
| Validity | Final Python verification: 72 cases, 70 passed and 2 full-DEM tests skipped; actual sample and independent reference comparisons; API and browser execution | Full owner-DEM reproduction, vertical-reference/provenance confirmation, uncertainty analysis, and independent rover-mobility evidence remain absent |
| Relevance | Mars terrain and route analysis directly support a planetary topography use case | Selected challenge and requirement-to-feature mapping remain missing; candidate Earth analog functionality is absent |
| Presentation | Normal-WebGL and no-WebGL real-backend scenarios passed, with regional route/profile rendering, error recovery, keyboard tabs and 390 px mobile checks | Produce an evidence-backed short demo, captions, source list, and limits slide in the actual required submission format |

Verification details are in [evidence/final_verification.json](evidence/final_verification.json). Passing tests supports the exercised behavior; it does not certify operational rover safety. The two browser scenarios used real Flask/Rasterio and the supplied equatorial sample while isolating external basemap requests. They do not verify NASA Trek availability or a public hosting environment.

## Demonstration content supported by actual execution

The real 256 × 256 sample supports a regional demo from **[0°, 0°] to [0.1°, 0.1°]**: the executed real-backend browser checks returned **8.667 km, 16 waypoints, and 25 valid profile samples**. Explain these as calculated DEM-scale outputs. The sample is regional, so a full-application `/readyz` 503 with regional capability is expected.

A separate, pixel-preserving **4 samples/degree public PDS reference**, not the owner's 128-samples/degree derivative, supported global checks: [0,179] → [0,−179] returned 118.316 km; [85,170] → [85,−170] returned 102.600 km; [35,10] → [−35,−170] returned 10,683.422 km against 10,648.428 km direct distance. See [evidence/global_reference_results.json](evidence/global_reference_results.json). Label the input switch and coarser source resolution explicitly; neither dataset represents a continuous rover-safe corridor.

The supplied sample matched 65,536/65,536 pixels in a nearest-neighbor virtual warp from a bounded public USGS COG window. That establishes an exact match for this window under that method, not the processing history or whole-file identity of the absent owner raster. See [evidence/usgs_sample_comparison.json](evidence/usgs_sample_comparison.json).

## Prioritized completion plan

1. Select and record the actual challenge; retrieve and retain its current statement, submission fields, and governing terms. Resolve the candidate relevance gap before claiming a complete answer.
2. Decide software distribution terms and resolve hero-image rights before external submission. Cite all datasets, libraries, imagery, and material AI assistance. Do not infer current terms from this report's indexed evidence.
3. Reproduce full-DEM boundary/global behavior with the actual original file; retain checksum, metadata, reference comparisons, and exact commands. Preserve unresolved vertical-reference and derivative-history questions.
4. Demonstrate one defensible user task using the executed regional case and explicitly separate global reference experiments. Include errors and limitations as part of the story.
5. Measure a small real user evaluation and prepare the official required artifacts after their format is verified. Keep Nivaan Raina's attribution and accurate AI disclosure intact.
