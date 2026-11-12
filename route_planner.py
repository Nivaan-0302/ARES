
import heapq
import math
import numpy as np
from geo_rules import align_longitude, contains_coordinate


TERRAIN_COSTS = (1.0, 3.0, 8.0, 20.0)


def hazard_cell_mask(hazard_grid):
    """Only the four exact declared classes are traversable.

    NaN, infinity, missing values, fractional codes and undeclared categories
    remain unknown. Do not truncate/cast them into an apparently safe class.
    """
    return np.isin(np.asarray(hazard_grid), (0, 1, 2, 3))


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
    if grid.ndim != 2 or min(grid.shape) == 0:
        raise ValueError('A hazard grid must be a nonempty two-dimensional array.')
    rows, cols = grid.shape
    available = hazard_cell_mask(grid)

    def valid(cell):
        r, c = cell
        return (
            isinstance(r, (int, np.integer))
            and isinstance(c, (int, np.integer))
            and 0 <= r < rows
            and 0 <= c < cols
            and available[r, c]
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
            # Destination-cell penalty is an illustrative, directional cost,
            # not travel time or a hard rover traversability constraint.
            step_cost = distance * TERRAIN_COSTS[hazard]

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

        # Preserve true centres through geometry/validation. Presentation may
        # round them, but premature rounding can leave very small pixels.
        coordinates.append([latitude, longitude])

    return coordinates


def coordinates_to_grid(latitude, longitude, bounds, grid_shape):
    """
    Convert Martian latitude/longitude into a terrain grid cell.

    Returns (row, column), or None if outside the region. Pixel coverage is
    west <= longitude < east and south < latitude <= north, matching a north-up
    raster's row/column indexing. Equivalent longitudes align to this window;
    an actual uncovered longitude gap is never clamped into the last column.
    """

    rows, cols = grid_shape

    north = bounds["north"]
    south = bounds["south"]
    west = bounds["west"]
    east = bounds["east"]

    if (rows <= 0 or cols <= 0 or not all(math.isfinite(v) for v in
            (latitude, longitude, north, south, west, east))
            or not (-90 <= latitude <= 90) or north <= south
            or not 0 < east-west <= 360):
        return None

    # Shift by whole turns only. Avoid modulo perturbations that could move an
    # exact east edge a few floating-point units into the preceding pixel.
    longitude = align_longitude(longitude, west, east)
    if not contains_coordinate(latitude, longitude, bounds):
        return None

    latitude_fraction = (north - latitude) / (north - south)
    longitude_fraction = (longitude - west) / (east - west)

    row = min(int(latitude_fraction * rows), rows - 1)
    col = min(int(longitude_fraction * cols), cols - 1)

    return (row, col)


def grid_route_with_endpoints(route, bounds, grid_shape, start, end):
    """Keep real endpoints without a centre detour inside a single grid cell.

    Other routes retain the screened cell-centre path and its endpoint
    connectors. Geometry remains a DEM-scale approximation, not a continuous
    traversability assessment.
    """
    if not route:
        return []
    if len(route) == 1:
        return [list(start), list(end)]
    return ([list(start)] + grid_route_to_coordinates(route, bounds, grid_shape)
            + [list(end)])


def great_circle_interpolate(start, end, fraction):
    """Position on the shortest spherical arc, with deterministic antipodes.

    Exactly antipodal endpoints have no unique shortest arc. In that case use
    the tangent toward the Cartesian axis least aligned with the start vector.
    """
    if not math.isfinite(fraction) or not 0 <= fraction <= 1:
        raise ValueError('Interpolation fraction must be between zero and one.')
    if fraction == 0:
        return list(start)
    if fraction == 1:
        return list(end)

    def unit(point):
        latitude, longitude = map(math.radians, point)
        return np.array([math.cos(latitude) * math.cos(longitude),
                         math.cos(latitude) * math.sin(longitude),
                         math.sin(latitude)], dtype=float)

    a, b = unit(start), unit(end)
    dot = max(-1., min(1., float(np.dot(a, b))))
    angle = math.acos(dot)
    tangent = b - dot * a
    magnitude = float(np.linalg.norm(tangent))
    if magnitude <= 1e-12:
        if dot > 0:
            vector = a
        else:
            axis = np.zeros(3)
            axis[int(np.argmin(np.abs(a)))] = 1.
            tangent = axis - np.dot(axis, a) * a
            tangent /= np.linalg.norm(tangent)
            vector = math.cos(math.pi * fraction) * a + math.sin(math.pi * fraction) * tangent
    else:
        tangent /= magnitude
        vector = math.cos(angle * fraction) * a + math.sin(angle * fraction) * tangent
    return [math.degrees(math.atan2(vector[2], math.hypot(vector[0], vector[1]))),
            math.degrees(math.atan2(vector[1], vector[0]))]


def calculate_route_distance(coordinates, *, round_digits=3):
    """
    Calculate the total surface distance along a route
    using the spherical Mars great-circle formula.

    Coordinates are [latitude, longitude] pairs.
    Returns distance in kilometres. The default retains the public three-decimal
    result; round_digits=None preserves precision for validation and metrics.
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

    return total_distance if round_digits is None else round(total_distance, round_digits)


