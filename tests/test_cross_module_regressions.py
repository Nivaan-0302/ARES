"""Independent regional routing invariants; no external DEM is required."""
import heapq
import math
from pathlib import Path
import random
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from route_planner import (astar_route, calculate_route_distance,
                           coordinates_to_grid, great_circle_interpolate,
                           grid_route_to_coordinates, mars_cell_distance_km)


def reference_cost(grid, start, goal, bounds):
    """Dijkstra oracle using the documented movement and cost policy."""
    weights = (1., 3., 8., 20.)
    rows, cols = grid.shape

    def available(cell):
        row, col = cell
        return 0 <= row < rows and 0 <= col < cols and 0 <= grid[cell] <= 3

    if not available(start) or not available(goal):
        return math.inf
    queue, costs = [(0., start)], {start: 0.}
    while queue:
        cost, cell = heapq.heappop(queue)
        if cost != costs[cell]:
            continue
        if cell == goal:
            return cost
        for row_change in (-1, 0, 1):
            for col_change in (-1, 0, 1):
                if row_change == col_change == 0:
                    continue
                other = (cell[0] + row_change, cell[1] + col_change)
                if not available(other):
                    continue
                if row_change and col_change and (
                        not available((cell[0] + row_change, cell[1])) or
                        not available((cell[0], cell[1] + col_change))):
                    continue
                candidate = cost + (mars_cell_distance_km(cell, other, bounds, grid.shape)
                                    * weights[int(grid[other])])
                if candidate < costs.get(other, math.inf):
                    costs[other] = candidate
                    heapq.heappush(queue, (candidate, other))
    return math.inf


class RegionalRoutingInvariants(unittest.TestCase):
    def test_astar_matches_dijkstra_with_physical_distances(self):
        generator = random.Random(42026)
        weights = (1., 3., 8., 20.)
        for latitude in (0., 65., 89.):
            bounds = {'north': latitude + .2, 'south': latitude - .2,
                      'west': 10., 'east': 10.5}
            for trial in range(12):
                grid = np.array([[generator.choice((-1, 0, 0, 1, 2, 3))
                                  for _ in range(7)] for _ in range(6)], dtype=np.int8)
                start, goal = (0, 0), (5, 6)
                grid[start] = grid[goal] = 0
                expected = reference_cost(grid, start, goal, bounds)
                with self.subTest(latitude=latitude, trial=trial):
                    route = astar_route(grid, start, goal, bounds=bounds)
                    if math.isinf(expected):
                        self.assertIsNone(route)
                    else:
                        self.assertIsNotNone(route)
                        self.assertEqual(route[0], start)
                        self.assertEqual(route[-1], goal)
                        actual = sum(mars_cell_distance_km(a, b, bounds, grid.shape)
                                     * weights[int(grid[b])]
                                     for a, b in zip(route, route[1:]))
                        self.assertAlmostEqual(actual, expected, places=10)

    def test_missing_cells_block_diagonal_corner_cutting(self):
        self.assertIsNone(astar_route([[0, -1], [-1, 0]], (0, 0), (1, 1)))

    def test_production_cell_centres_round_trip(self):
        bounds = {'north': 68.5, 'south': 68., 'west': -30.25, 'east': -29.75}
        shape = (64, 64)
        cells = [(row, col) for row in range(shape[0]) for col in range(shape[1])]
        coordinates = grid_route_to_coordinates(cells, bounds, shape)
        self.assertEqual([coordinates_to_grid(*point, bounds, shape) for point in coordinates], cells)
        self.assertIsNone(coordinates_to_grid(69., -30., bounds, shape))

    def test_geodesic_subdivision_preserves_precise_distance(self):
        for start, end in (([80., -10.], [80., 10.]), ([0., 179.], [0., -179.]),
                           ([-35., -36.], [-35.2, -35.8])):
            with self.subTest(start=start, end=end):
                middle = great_circle_interpolate(start, end, .5)
                direct = calculate_route_distance([start, end], round_digits=None)
                halves = calculate_route_distance([start, middle, end], round_digits=None)
                self.assertAlmostEqual(direct, halves, places=9)
                self.assertAlmostEqual(calculate_route_distance([start, middle], round_digits=None),
                                       direct / 2, places=9)


if __name__ == '__main__':
    unittest.main()
