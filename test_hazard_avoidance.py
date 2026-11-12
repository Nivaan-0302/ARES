"""Synthetic assertions against production routing and risk reporting."""
import unittest
from route_planner import astar_route


class HazardAvoidanceTests(unittest.TestCase):
    def test_weighted_route_avoids_extreme_block_when_detour_exists(self):
        grid = [[0] * 7 for _ in range(7)]
        for row in range(2, 5):
            for col in range(2, 5):
                grid[row][col] = 3
        start, goal = (3, 0), (3, 6)
        route = astar_route(grid, start, goal)
        self.assertIsNotNone(route)
        self.assertEqual(route[0], start)
        self.assertEqual(route[-1], goal)
        self.assertTrue(all(grid[row][col] != 3 for row, col in route))

    def test_production_report_uses_illustrative_risk_index(self):
        from mission_routing import regional_route
        # A one-row corridor forces known production path cells.
        region = {"hazard_grid": [[0] * 5 + [1] * 3 + [2] * 2],
                  "bounds": {"north": 1., "south": 0., "west": 0., "east": 10.}}
        result = regional_route([.5, .5], [.5, 9.5], region)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["hazard_breakdown"],
                         {"low": 5, "moderate": 3, "high": 2, "extreme": 0})
        self.assertEqual(result["terrain_risk_score"], 15.)


if __name__ == "__main__":
    unittest.main()
