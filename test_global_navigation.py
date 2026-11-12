"""Synthetic global-routing regressions; never open the MOLA raster."""
import unittest
from unittest.mock import patch
import numpy as np
import global_navigation as nav


class GlobalNavigationTests(unittest.TestCase):
    def test_flat_grid_routes_have_exact_endpoints(self):
        model = (np.zeros((nav.HEIGHT, nav.WIDTH)),
                 np.zeros((nav.HEIGHT, nav.WIDTH), dtype=np.int8))
        original_model = nav.global_model
        with patch.object(nav, "global_model", return_value=model):
            for coordinates in ((0, 0, 0, 10), (0, 179, 0, -179),
                                (80, -120, -70, 75), (0, 0, 0, 0)):
                with self.subTest(coordinates=coordinates):
                    result = nav.plan(*coordinates)
                    self.assertEqual(result["status"], "success", result)
                    self.assertEqual(result["route_coordinates"][0], list(coordinates[:2]))
                    self.assertEqual(result["route_coordinates"][-1], list(coordinates[2:]))
                    # Reported distances are rounded to 0.001 km.
                    self.assertGreaterEqual(result["route_distance_km"] + .002,
                                            result["direct_distance_km"])
        self.assertIs(nav.global_model, original_model)

    def test_missing_endpoint_data_is_not_traversable(self):
        hazard = np.zeros((nav.HEIGHT, nav.WIDTH), dtype=np.int8)
        hazard[nav.cell_for(0, 0)] = -1
        with patch.object(nav, "global_model", return_value=(np.zeros_like(hazard), hazard)):
            result = nav.plan(0, 0, 0, 10)
        self.assertEqual(result["status"], "no_data")


if __name__ == "__main__":
    unittest.main()
