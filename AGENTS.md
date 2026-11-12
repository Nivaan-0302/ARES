# ARES — Codex Development Instructions

## Project identity
ARES is a Mars terrain intelligence and mission-planning application.

**Creator and Project Lead:** Nivaan Raina

## Primary objective
Improve ARES into a scientifically credible, reliable, polished NASA Space Apps competition submission while preserving its existing working capabilities.

## Mandatory development rules

1. **Preserve functionality.** Do not remove or rewrite working features without explicit approval.
2. **Work incrementally.** Inspect relevant files before editing, make focused changes, and explain what changed.
3. **Protect scientific integrity.** Clearly distinguish measured terrain data, calculated estimates, simulated results, and assumptions.
4. **Protect the dataset.** Never delete, overwrite, commit, or redistribute the original NASA MOLA DEM without explicit authorization.
5. **Preserve routing.** Maintain existing regional A*, global navigation, terrain hazard analysis, and route refinement functionality.
6. **Preserve the interface.** Maintain the Mars globe, map, dashboards, and existing interactive controls.
7. **Avoid invented results.** Never fabricate test outcomes, scientific accuracy, competition results, or performance metrics.
8. **Validate changes.** Run relevant available tests when possible and report any tests that could not be executed.
9. **Protect attribution.** Retain Nivaan Raina as creator and project lead. Maintain accurate AI-assistance disclosures.
10. **Avoid destructive operations.** Do not delete project files, reset Git history, change licensing, publish the repository, or deploy the application without explicit approval.
11. **Respect dependencies.** Do not add libraries or change Python dependencies unnecessarily.
12. **Maintain documentation.** Update the README when functionality, limitations, installation instructions, or scientific methods materially change.

## Scientific limitations
ARES uses NASA MOLA elevation data. Terrain resolution, interpolation, hazard classification, and routing assumptions must be communicated accurately.

Do not describe ARES as flight-qualified, rover-certified, or suitable for operational mission safety decisions.

## Development workflow
Before each substantial modification:

1. Identify the affected files and existing behavior.
2. Explain the proposed change and possible risks.
3. Implement the smallest reliable improvement.
4. Validate relevant functionality.
5. Summarize changes and remaining limitations.

Prioritize scientific credibility, reliable functionality, transparent methodology, and a polished user experience.