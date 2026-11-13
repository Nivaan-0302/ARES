# Evidence-backed submission and demo guide

**Creator and Project Lead:** Nivaan Raina. The actual Space Apps challenge remains unselected. This guide proposes presentation content; it is not an eligibility decision, a required video format, or a claim of competition success.

## Resolve the challenge before finalizing the pitch

Read [COMPETITION_READINESS.md](COMPETITION_READINESS.md) for the actual official-source access results: live event/challenges/legal/candidate fetches failed, while a search service returned indexed official-domain text. Obtain the current challenge statement, required submission fields, deadline/time zone, judging instructions, and governing terms from the actual event before submission.

The candidate Earth-analog challenge requires terrestrial analog identification and characterization. ARES currently supplies Mars terrain/routing capabilities and no Earth-analog workflow. Either select a verified challenge matching this implemented scope or explicitly plan a small comparative analog study; do not label a Mars-only demo a complete analog-finding solution.

Record the official challenge title/URL, target user, specific task, requirement-to-feature mapping, contribution beyond ordinary A*, evidence of utility, remaining limits, and required artifacts. Exact slide count, video length, scoring weights, and submission deadlines were not independently verified.

## A proposed short demo, using actual executed cases

The narrative is: **“A planner can inspect how DEM-scale topography affects an illustrative Mars route, compare objectives, and see where the data cannot support a conclusion.”** Do not claim rover certification, live mission telemetry, travel time, energy, or failure probability.

1. **Explain the data and question.** Name Nivaan Raina as creator/project lead. Distinguish the real equatorial sample, public reference products, estimated slopes, class assumptions, and simulated tests. State that the original full raster is unavailable in this execution environment.
2. **Show regional exploration.** Configure the supplied 256 × 256 sample. From [0°,0°] to [0.1°,0.1°], the executed real-Flask browser checks produced **8.667 km, 16 waypoints, and 25 valid elevation-profile samples**. Show consistent map/globe endpoints, the profile, estimated classes, and the actual comparison if available. Do not promise hazard avoidance where no measured comparison establishes it.
3. **Interpret scope.** Explain that classes are illustrative DEM-scale slope thresholds and EXTREME has a finite routing penalty. Distances are calculated surface geometry; the risk index is not failure probability. A regional sample correctly leaves full-app `/readyz` at 503 with regional capability.
4. **Show scale changes honestly.** Use the separately prepared public 4 samples/degree PDS reference for a global experiment. The executed dateline case [0,179] → [0,−179] returned **118.316 km**. Label this different input and the 1° averaged planning grid. Selected local refinement windows do not continuously certify the route.
5. **Show a failure case.** With the regional sample, a distant destination [50°,50°] was exercised as unavailable; the UI exposed retry and cleared stale route guidance. Demonstrate missing-data/error interpretation, not a fabricated successful fallback route.
6. **Close with evidence and limits.** Show actual test/comparison results, source citations, and the remaining full-DEM/provenance/challenge/rights work. Credit material AI assistance accurately. Use captions, readable units, keyboard operation, and a concise explanation of the user's decision.

The real-backend checks exercised normal WebGL and a no-WebGL 2D fallback, blocked external basemap requests, and checked 390 px mobile width and keyboard tabs. These are evidence of those interactions, not proof that every device or the external NASA tile service works.

## Submission packet

- Current selected challenge statement and a one-page requirement-to-evidence mapping.
- Reproducible source/setup, tested dependencies, exact demo inputs and checksums, and actual scientific/API/browser verification outputs.
- Official dataset/product citations, labels, coordinate/reference assumptions, derivative-history uncertainties, and independent comparison method.
- A clear account of what Nivaan Raina directed and what AI tools assisted with; original creator attribution and history remain intact.
- Resolved hero-image rights or an explicitly approved replacement; source list and third-party notices.
Original ARES software is licensed under MIT; see ../LICENSE. Third-party asset rights require separate review.
- The required pitch/video/project fields only after their actual format and rights conditions are verified.

Do not fabricate user feedback, impact metrics, scientific accuracy, challenge selection, eligibility, development dates, or awards. Keep failures/skips and dataset limitations visible beside successes.
