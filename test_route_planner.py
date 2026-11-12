
from terrain_region import analyze_region
from route_planner import astar_route, grid_route_to_coordinates

print("ARES — AUTONOMOUS ROUTE PLANNING TEST")
print("------------------------------------")

# Analyze real NASA MOLA terrain near Mars's equator
terrain = analyze_region(0, 0)

hazard_grid = terrain["hazard_grid"]

# Grid coordinates: (row, column)
start = (5, 5)
goal = (55, 55)

print("Terrain grid:", len(hazard_grid), "x", len(hazard_grid[0]))
print("Starting cell:", start)
print("Destination cell:", goal)


route = astar_route(
    hazard_grid,
    start,
    goal,
    bounds=terrain["bounds"]
)


if route is None:
    print("RESULT: No traversable route found.")
else:
    print("RESULT: Route successfully calculated!")
    print("Number of cells in route:", len(route))
    print("Starting point:", route[0])
    print("Ending point:", route[-1])

    hazards_encountered = [
        hazard_grid[row][col]
        for row, col in route
    ]

    print("Maximum hazard level:", max(hazards_encountered))
    print("Route:", route)


def grid_route_to_coordinates(route, bounds, grid_shape):
    """
    Convert A* grid cells into Martian latitude/longitude.

    route: List of (row, column) coordinates
    bounds: Geographic bounds returned by terrain_region.py
    grid_shape: (rows, columns)
    """

    rows, cols = grid_shape

    north = bounds["north"]
    south = bounds["south"]
    west = bounds["west"]
    east = bounds["east"]

    latitude_step = (north - south) / rows
    longitude_step = (east - west) / cols

    coordinates = []

    for row, col in route:
        # Grid row 0 represents the northernmost row.
        latitude = north - (row + 0.5) * latitude_step

        # Grid column 0 represents the westernmost column.
        longitude = west + (col + 0.5) * longitude_step

        coordinates.append([
            round(latitude, 6),
            round(longitude, 6)
        ])

    return coordinates


# Convert the A* route into Martian coordinates
if route is not None:
    coordinates = grid_route_to_coordinates(
        route,
        terrain["bounds"],
        (len(hazard_grid), len(hazard_grid[0]))
    )

    print("\nARES — GEOGRAPHIC ROUTE TEST")
    print("-----------------------------")
    print("Total geographic waypoints:", len(coordinates))
    print("Starting coordinates:", coordinates[0])
    print("Destination coordinates:", coordinates[-1])

    # Check that every waypoint lies inside the analyzed region
    bounds = terrain["bounds"]

    valid = all(
        bounds["south"] <= lat <= bounds["north"]
        and bounds["west"] <= lon <= bounds["east"]
        for lat, lon in coordinates
    )

    print("All waypoints within terrain bounds:", valid)

