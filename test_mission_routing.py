"""Run with: python3 -m unittest test_mission_routing -v"""
import unittest
from unittest.mock import patch
import numpy as np
from global_navigation import great_circle, plan
from mission_routing import validate_coordinates, route_metrics, calculate_mission_route


class MissionRoutingTests(unittest.TestCase):
    def test_rejects_invalid_and_nonfinite_coordinates(self):
        for values in ((91, 0, 0, 0), (0, -181, 0, 0), (float('nan'), 0, 0, 0)):
            with self.assertRaises(ValueError):
                validate_coordinates(values)

    def test_exact_endpoints_and_efficiency(self):
        start, end = [-35.7, -36.3], [-35.6, -36.2]
        coords = [start, [-35.65, -36.3], end]
        metrics = route_metrics(coords, start, end)
        self.assertLess(metrics['route_efficiency_percent'], 100)
        self.assertGreater(metrics['route_distance_km'], metrics['direct_distance_km'])
        with self.assertRaises(ValueError):
            route_metrics([[0, 0], end], start, end)

    def test_same_point_is_zero_distance(self):
        metrics = route_metrics([[10, 20], [10, 20]], [10, 20], [10, 20])
        self.assertEqual(metrics['route_distance_km'], 0)
        self.assertEqual(metrics['route_efficiency_percent'], 100)

    def test_global_antimeridian_and_exact_endpoints(self):
        with patch('global_navigation.global_model', return_value=(np.zeros((180, 360)), np.zeros((180, 360), dtype=np.int8))):
            result = plan(0, 179, 0, -179)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['route_coordinates'][0], [0, 179])
        self.assertEqual(result['route_coordinates'][-1], [0, -179])
        self.assertGreaterEqual(result['route_distance_km'], result['direct_distance_km'])
        self.assertLess(result['route_distance_km'], 500)

    def test_global_opposite_hemispheres(self):
        with patch('global_navigation.global_model', return_value=(np.zeros((180, 360)), np.zeros((180, 360), dtype=np.int8))):
            result = plan(35, 10, -35, -170)
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['route_distance_km'], 1000)
        self.assertEqual(result['route_coordinates'][-1], [-35, -170])

    def test_regional_route_uses_actual_coordinates(self):
        fake_region = {'bounds': {'north': 0.25, 'south': -0.25, 'west': -0.25, 'east': 0.25},
                       'hazard_grid': np.zeros((64, 64), dtype=np.int8).tolist()}
        fake_profile = [{'distance_km': 0, 'elevation_m': 0, 'slope_degrees': 1},
                        {'distance_km': 1, 'elevation_m': 2, 'slope_degrees': 2}]
        with patch('mission_routing.analyze_region', return_value=fake_region), patch('mission_routing.elevation_profile', return_value=fake_profile):
            result = calculate_mission_route(0.01, 0.01, 0.1, 0.1)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['route_coordinates'][0], [0.01, 0.01])
        self.assertEqual(result['route_coordinates'][-1], [0.1, 0.1])
        self.assertEqual(result['scientific_report']['route_distance_km'], result['route_distance_km'])
        self.assertEqual(result['scientific_report']['slope_sample_count'], 2)


if __name__ == '__main__':
    unittest.main()
