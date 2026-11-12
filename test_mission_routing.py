"""Run with: python3 -m unittest test_mission_routing -v"""
import unittest
from unittest.mock import patch
import numpy as np
from global_navigation import great_circle, plan
from mission_routing import validate_coordinates, route_metrics, calculate_mission_route
from mission_routing import regional_route, make_scientific_report
from route_planner import calculate_route_distance
from dem_data import DEMValidationError


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

    def test_direct_route_uses_precision_before_rounding(self):
        # These lengths round downward; rounded input previously caused a false
        # "shorter than great-circle" error for valid coordinates.
        for longitude in (.3, .4, .000001):
            start, end = [0, 0], [0, longitude]
            metrics = route_metrics([start, end], start, end)
            self.assertEqual(metrics['route_efficiency_percent'], 100)
            self.assertEqual(metrics['distance_increase_percent'], 0)
            self.assertAlmostEqual(calculate_route_distance([start, end], round_digits=None),
                                   great_circle(start, end), places=8)

    def test_same_cell_does_not_add_a_centre_detour(self):
        region = {'bounds': {'north': .25, 'south': -.25, 'west': -.25, 'east': .25},
                  'hazard_grid': np.zeros((64, 64), dtype=np.int8).tolist()}
        start, end = [.001, .001], [.001, .001001]
        result = regional_route(start, end, region)
        self.assertEqual(result['route_coordinates'], [start, end])
        self.assertEqual(result['hazard_breakdown']['low'], 1)
        metrics = route_metrics(result['route_coordinates'], start, end)
        self.assertEqual(metrics['route_efficiency_percent'], 100)
        self.assertLess(calculate_route_distance(result['route_coordinates'], round_digits=None), .001)

    def test_missing_same_cell_still_rejects_route(self):
        region = {'bounds': {'north': .25, 'south': -.25, 'west': -.25, 'east': .25},
                  'hazard_grid': np.full((64, 64), -1, dtype=np.int8).tolist()}
        self.assertEqual(regional_route([.001, .001], [.001, .001001], region)['status'], 'no_route')

    def test_full_global_mission_rounding_and_single_profile(self):
        import route_refinement as rr
        synthetic = (np.zeros((180, 360)), np.zeros((180, 360), dtype=np.int8))
        # Missing optional refinement data must not invalidate the coarse route.
        # Its scientific report is built once by the final mission workflow.
        with patch('global_navigation.global_model', return_value=synthetic), \
             patch.object(rr, 'analyze_region', side_effect=ValueError('Synthetic unavailable window')), \
             patch.object(rr, 'elevation_profile') as redundant_profile, \
             patch('mission_routing.elevation_profile', return_value=[]) as final_profile:
            result = calculate_mission_route(0, 0, 0, .3)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['route_coordinates'], [[0., 0.], [0., .3]])
        self.assertEqual(result['route_distance_km'], 17.747)
        self.assertEqual(result['route_efficiency_percent'], 100)
        self.assertEqual(result['refinement']['sampled_windows'], 0)
        self.assertEqual(result['refinement']['unavailable_windows'], 1)
        redundant_profile.assert_not_called()
        final_profile.assert_called_once_with(result['route_coordinates'], samples=25)

    def test_optional_profile_failure_keeps_valid_route_and_discloses_gap(self):
        start, end = [0, 0], [0, .3]
        result = {'status': 'success', 'hazard_breakdown': {'low': 2}, 'terrain_risk_score': 0,
                  **route_metrics([start, end], start, end)}
        with patch('mission_routing.elevation_profile', side_effect=DEMValidationError('/private/example/dem.tif changed during sampling')):
            result = make_scientific_report(result, [start, end])
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['scientific_report']['elevation_sample_count'], 0)
        self.assertIn('Elevation profile unavailable', result['scientific_report']['limitations'])
        self.assertNotIn('/private/',str(result))

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
