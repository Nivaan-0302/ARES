# Initial submission-readiness audit

This report was prepared before the submission-readiness implementation. Review base: `ac6910c55b48cef39198cd7cfaaf2658e69c3ad2`, following the authorized merge of PR #2. Scope: all tracked source, documentation, HTML/CSS/JavaScript, Python routing/science/API modules, tests, dependency manifests, licensing, image assets, and setup/deployment instructions. Findings below describe that initial state; completion is recorded separately in [SUBMISSION_READINESS.md](SUBMISSION_READINESS.md).

## Findings and intended corrections

| Priority | Finding and evidence | Smallest useful action |
| --- | --- | --- |
| High | README and competition/submission guides say the challenge is unselected and discuss Earth analogs as the active candidate. The owner has selected **Interplanetary Survival Guide: Martian Map**. | Identify the selected challenge, add an evidence-linked alignment matrix, keep old candidate/access research explicitly historical. |
| High | Official challenge title/URL is indexed, but direct statement retrieval fails (503; independent reader 502). An institutional event page reproduces an overview. | Separate verified title, secondary overview and unverified detailed requirements; never invent eligibility, deadline, or challenge requirements. |
| High | Full original DEM and historical 256×256 sample are absent here. Historical full-owner verification and two regional smoke passes are recorded in the later scientific addenda. | Distinguish current workspace checks from owner records and historical sample/reference checks. Do not claim a new full-DEM run. |
| Medium | Current asset/input summaries still request a hash or call the image replacement an option, despite later owner hash verification, MIT selection and NASA image replacement. | Update current registers and add history banners; preserve dated evidence packets and all original results. |
| Medium | README has no screenshots, architecture diagram, challenge matrix or coherent judging path. No screenshots/media gallery is tracked. | Build a concise landing page and actual-interface gallery, with dataset labels, provenance and limitations. |
| Medium | Scientific detail is distributed across overlapping historical reports. Weighted grid cost, route connectors, risk class counts and sparse refinement need a clearer explanation. | Add focused methodology/routing/limitations documents with source links, preserving the 5/15/25° categories and existing implementations. |
| Low | `experiment10_hale.py` calls a heap-based distance-only Dijkstra search “Distance-only A*”. | Correct its diagnostic label only; no algorithm change. |
| Low | README hard-break backslash and report XML-namespace false positive / relative links in PR #2. | Corrected during PR review; eight Node regressions, JS syntax, whitespace and executable-text comparisons passed before merge. |

## Code, UI and dependency review

Regional A*, same-grid Dijkstra comparison, global 1° routing, bounded local refinement, central-axial slope calculations, valid-data masks, private dataset serving restrictions and shared frontend mission state are present. No replacement or functional rewrite is indicated by this audit. Existing tests cover coordinate rejection, masks/unknowns, diagonal corners, dateline/polar geometry, stale requests, WebGL fallback and errors. No environmental forecasting, radiation, life-support, astronaut mobility or EVA constraint model was found.

Python 3.12.14, NumPy, Node, Playwright and Chromium are initially available; Flask/Rasterio are initially missing. Use an isolated environment and the repository manifests. Retain the historic exact pins even if a compatible-range environment is needed; report actual installed versions. NASA basemap requests are external dependencies, separate from scientific elevation data.

Read-only preliminary checks: all Python sources parsed; eight Node regressions and both synthetic browser scenarios passed. Synthetic API scenarios establish interface behavior, not MOLA science. Backend and screenshot checks require actual identified raster inputs.

## Documentation, links and rights

Protected attribution/history/instruction files, MIT and upstream license notices are present. NASA/JPL-Caltech hero-image source and conversion are recorded. The current asset register has malformed blank-separated table rows and stale descriptions. Historical documents are useful evidence, not redundant files to delete. Clarify the current reading path and add banners rather than erasing them.

Local file-target scan found quoted links in the date-reference report resolving relative to the wrong directory; corrected in PR #2. Anchor targets, external source availability and the rewritten documentation will be checked again after changes. Scientific/reference sources and NASA Trek service availability must be reported separately from internal link correctness. No hosting deployment, public release, registration or submission is authorized or claimed by this audit.

## Work plan and limits

1. Preserve the already reviewed PR #2 merge and its real timestamps.
2. Refresh challenge/readiness documents with source-access evidence and historical context.
3. Produce methodology, algorithm, limitations and architecture explanations tied to real source.
4. Capture seven actual browser views using a separately downloaded, hash-verified native PDS 4 ppd reference if accessible; label its coarse resolution and keep the raster outside source control.
5. Rewrite the README, run applicable backend/frontend/browser/link/license checks, and provide a reviewable follow-up PR.

The supplied master directive ends mid-sentence during Task 12. This work covers its supplied Tasks 1–12 and does not infer extra publication, competition-submission or deployment instructions.
