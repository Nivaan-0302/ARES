
import heapq
import math
import numpy as np


def mars_cell_distance_km(cell_a, cell_b, bounds, grid_shape):
    """
    Calculate approximate surface distance between
    two MOLA grid-cell centres on Mars.
    """

    rows, cols = grid_shape

    north = bounds["north"]
    south = bounds["south"]
    west = bounds["west"]
    east = bounds["east"]

    lat_step = (north - south) / rows
    lon_step = (east - west) / cols

    r1, c1 = cell_a
    r2, c2 = cell_b

    lat1 = math.radians(north - (r1 + 0.5) * lat_step)
    lat2 = math.radians(north - (r2 + 0.5) * lat_step)

    lon1 = math.radians(west + (c1 + 0.5) * lon_step)
    lon2 = math.radians(west + (c2 + 0.5) * lon_step)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    a = max(0.0, min(1.0, a))

    return 2 * 3389.5 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

def astar_route(hazard_grid, start, goal, bounds=None):
    """
    A* pathfinding across a terrain hazard grid.

    start and goal are (row, column) coordinates.
    Returns a list of grid cells, or None if no path exists.
    """

    grid = np.asarray(hazard_grid)
    rows, cols = grid.shape

    # Illustrative terrain costs, not rover-specific limits
    terrain_costs = {
        0: 1.0,    # LOW
        1: 3.0,    # MODERATE
        2: 8.0,    # HIGH
        3: 20.0   # EXTREME
    }

    def valid(cell):
        r, c = cell
        return (
            0 <= r < rows
            and 0 <= c < cols
            and int(grid[r, c]) in terrain_costs
        )

    if not valid(start) or not valid(goal):
        return None

    def heuristic(cell):
        # Octile distance: appropriate for 8-direction movement
        dr = abs(cell[0] - goal[0])
        dc = abs(cell[1] - goal[1])
        return max(dr, dc) + (math.sqrt(2) - 1) * min(dr, dc)

    directions = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]
    if bounds is not None:
        def heuristic(cell):
            return mars_cell_distance_km(
                cell, goal, bounds, (rows, cols)
            )
    frontier = [(heuristic(start), 0.0, start)]
    came_from = {}
    best_cost = {start: 0.0}

    while frontier:
        _, current_cost, current = heapq.heappop(frontier)

        if current_cost > best_cost.get(current, math.inf):
            continue

        if current == goal:
            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            return path[::-1]

        for dr, dc in directions:
            neighbor = (current[0] + dr, current[1] + dc)

            if not valid(neighbor):
                continue

            # Prevent diagonal movement through blocked corners
            if dr != 0 and dc != 0:
                side_a = (current[0] + dr, current[1])
                side_b = (current[0], current[1] + dc)

                if not valid(side_a) or not valid(side_b):
                    continue

           
            if bounds is not None:
                distance = mars_cell_distance_km(
                    current, neighbor, bounds, (rows, cols)
                )
            else:
                distance = math.hypot(dr, dc)

            hazard = int(grid[neighbor])
            step_cost = distance * terrain_costs[hazard]

            new_cost = current_cost + step_cost

            if new_cost < best_cost.get(neighbor, math.inf):
                best_cost[neighbor] = new_cost
                came_from[neighbor] = current

                priority = new_cost + heuristic(neighbor)

                heapq.heappush(
                    frontier,
                    (priority, new_cost, neighbor)
                )

    return None


def grid_route_to_coordinates(route, bounds, grid_shape):
    rows, cols = grid_shape

    north = bounds["north"]
    south = bounds["south"]
    west = bounds["west"]
    east = bounds["east"]

    latitude_step = (north - south) / rows
    longitude_step = (east - west) / cols

    coordinates = []

    for row, col in route:
        latitude = north - (row + 0.5) * latitude_step
        longitude = west + (col + 0.5) * longitude_step

        coordinates.append([
            round(latitude, 6),
            round(longitude, 6)
        ])

    return coordinates


def coordinates_to_grid(latitude, longitude, bounds, grid_shape):
    """
    Convert Martian latitude/longitude into a terrain grid cell.

    Returns (row, column), or None if outside the region.
    """

    rows, cols = grid_shape

    north = bounds["north"]
    south = bounds["south"]
    west = bounds["west"]
    east = bounds["east"]

    # Reject coordinates outside the analyzed region
    if not (south <= latitude <= north):
        return None

    if not (west <= longitude <= east):
        return None

    latitude_fraction = (north - latitude) / (north - south)
    longitude_fraction = (longitude - west) / (east - west)

    row = min(int(latitude_fraction * rows), rows - 1)
    col = min(int(longitude_fraction * cols), cols - 1)

    return (row, col)


def calculate_route_distance(coordinates):
    """
    Calculate the total surface distance along a route
    using the spherical Mars great-circle formula.

    Coordinates are [latitude, longitude] pairs.
    Returns distance in kilometres.
    """

    import math

    MARS_RADIUS_KM = 3389.5
    total_distance = 0.0

    for i in range(len(coordinates) - 1):
        lat1, lon1 = coordinates[i]
        lat2, lon2 = coordinates[i + 1]

        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(delta_lon / 2) ** 2
        )

        a = max(0.0, min(1.0, a))

        central_angle = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        total_distance += MARS_RADIUS_KM * central_angle

    return round(total_distance, 3)


