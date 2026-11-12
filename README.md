# ARES — Mars Terrain Intelligence & Mission Planning

**Interactive Mars Terrain Analysis and Mission Planning System**

**Creator and Project Lead:** Nivaan Raina  
**Copyright:** © 2026 Nivaan Raina  
**Project:** NASA Space Apps Challenge 2026  
**Status:** Functional research and educational prototype

## Overview

ARES is an interactive Mars terrain-intelligence and mission-planning system that combines planetary elevation data, terrain analysis, and computational pathfinding to support exploration planning.

The system enables users to explore Mars, examine terrain conditions, evaluate potential routes, and compare navigation strategies through an integrated mission-control interface.

## Core Capabilities

- Interactive 3D Mars globe and planetary mapping
- NASA MOLA elevation-data integration
- Elevation and slope analysis
- Regional terrain hazard classification
- Terrain-aware A* route planning
- Coarse global navigation and route refinement
- Route strategy comparison
- Elevation profiles and scientific visualizations
- Mission Decision Brief and mission-control dashboards

## Scientific Methodology

ARES uses elevation information from the Mars Orbiter Laser Altimeter (MOLA), associated with NASA's Mars Global Surveyor mission.

Terrain analysis uses elevation sampling and slope estimation. Regional terrain hazards are classified using slope-based thresholds.

Regional navigation uses the A* search algorithm to evaluate routes with distance and terrain-related traversal costs. Global navigation operates at a coarser resolution, with regional refinement where supported.

These methods demonstrate computational approaches to planetary exploration planning. They are not a substitute for flight-qualified rover navigation.

## Technical Architecture

**Backend:** Python, Flask, NumPy, Rasterio

**Frontend:** HTML, CSS, JavaScript, Leaflet, Three.js

**Core backend modules:** `terrain_api.py`, `terrain_region.py`, `route_planner.py`, `global_navigation.py`, `mission_routing.py`, `route_refinement.py`, `phase5_comparison.py`

## Installation

Install the Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Place the NASA MOLA elevation raster at:

```text
data/mola128_mola64_merge_90Nto90S_SimpleC_clon0.tif
```

Start ARES:

```bash
python3 terrain_api.py
```

Open `http://127.0.0.1:5001` in your browser, provided the application is configured to use that port.

The development environment uses Flask 3.1.3, NumPy 2.5.4, and Rasterio 1.5.2.

The approximately 2 GB MOLA raster is not included in the source repository. Its authoritative download location and full citation must be documented before publication.

## Testing and Validation

ARES has undergone testing of elevation sampling, terrain classification, regional and global navigation, route refinement, and route comparison.

A separate synthetic validation run recorded **15 passing test cases**, providing evidence of the algorithmic behaviors examined.

The repository includes supporting test scripts and development experiments.

## Scientific Limitations

ARES is a research and educational prototype. Its analysis is limited by terrain-data resolution, simplified hazard classification, coarse global routing, and the absence of detailed rover-specific mobility and environmental models.

ARES does not provide flight-qualified navigation or guarantee that a calculated route is safe for a real rover.

## Project Authorship

ARES is an independently directed solo project created by **Nivaan Raina**.

The creator established the project's objectives, selected its capabilities, directed design and development decisions, tested its functionality, and evaluated its results.

See `AUTHORS.md`, `COPYRIGHT`, and `DEVELOPMENT_HISTORY.md` for additional project records.

## AI Assistance and Attribution

ChatGPT was used as a development-support tool for code generation and refinement, interface implementation, debugging, technical explanations, and documentation.

The project's objectives, feature selection, development direction, evaluation, and final submission are directed by its creator.

ARES performs terrain analysis and route planning using computational algorithms operating on NASA MOLA elevation data, rather than generating routes through a conversational AI model.

Any AI-generated visual assets must be identified and disclosed according to applicable competition requirements.

## Copyright and Licensing

**Copyright © 2026 Nivaan Raina.**

The original project material is subject to the open-source license selected for distribution. NASA datasets, third-party software, and externally sourced assets retain their respective rights.

A `LICENSE` file will be added after confirming the applicable competition requirements.

## Project Vision

ARES explores how planetary geospatial intelligence and computational navigation can support more informed mission planning and future autonomous exploration systems.

---

**ARES — Created by Nivaan Raina**  
**© 2026 Nivaan Raina**