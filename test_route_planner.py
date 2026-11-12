"""Production coordinate conversion tests and optional real-MOLA routing check."""
from pathlib import Path
import unittest
import numpy as np
from dem_data import DEM_PATH
from route_planner import astar_route, coordinates_to_grid, grid_route_to_coordinates


class CoordinateConversionTests(unittest.TestCase):
    def test_production_cell_centres_round_trip(self):
        bounds = {"north": 1., "south": 0., "west": 10., "east": 12.}
        cells = [(0, 0), (0, 3), (1, 2)]
        coordinates = grid_route_to_coordinates(cells, bounds, (2, 4))
        self.assertEqual(coordinates, [[.75, 10.25], [.75, 11.75], [.25, 11.25]])
        self.assertEqual([coordinates_to_grid(*point, bounds, (2, 4))
                          for point in coordinates], cells)

    def test_outside_region_is_rejected(self):
        bounds = {"north": 1., "south": 0., "west": 10., "east": 12.}
        for point in ((1.1, 11), (-.1, 11), (.5, 9.9), (.5, 12.1)):
            with self.subTest(point=point):
                self.assertIsNone(coordinates_to_grid(*point, bounds, (2, 4)))


@unittest.skipUnless(Path(DEM_PATH).is_file(), "NASA MOLA DEM is not supplied; set ARES_DEM_PATH")
class RealRoutePlannerTests(unittest.TestCase):
    def test_real_route_is_connected_and_inside_region(self):
        from terrain_region import analyze_region
        terrain = analyze_region(0, 0)
        grid = np.asarray(terrain["hazard_grid"])
        start, goal = (5, 5), (55, 55)
        self.assertGreaterEqual(grid[start], 0, "Reference start has missing data")
        self.assertGreaterEqual(grid[goal], 0, "Reference destination has missing data")
        route = astar_route(grid, start, goal, bounds=terrain["bounds"])
        self.assertIsNotNone(route, "Reference equatorial integration route is unavailable")
        self.assertEqual(route[0], start)
        self.assertEqual(route[-1], goal)
        self.assertTrue(all(grid[row, col] >= 0 for row, col in route))
        for a, b in zip(route, route[1:]):
            self.assertLessEqual(max(abs(a[0]-b[0]), abs(a[1]-b[1])), 1)
        coordinates = grid_route_to_coordinates(route, terrain["bounds"], grid.shape)
        self.assertEqual([coordinates_to_grid(*point, terrain["bounds"], grid.shape)
                          for point in coordinates], route)


if __name__ == "__main__":
    unittest.main()
