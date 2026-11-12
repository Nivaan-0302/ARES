"""Tests of bounded route refinement, independent of the 2 GB DEM."""
import unittest
from unittest.mock import patch
import numpy as np
import route_refinement as rr
from global_navigation import great_circle
from phase5_comparison import summarize


class RefinementTests(unittest.TestCase):
    def test_dateline_interpolation(self):
        p=rr.interpolate([0,179],[0,-179],.5)
        self.assertAlmostEqual(abs(p[1]),180)

    def test_interpolation_follows_geodesic_at_high_latitude(self):
        start, end = [80, -10], [80, 10]
        midpoint = rr.interpolate(start, end, .5)
        self.assertAlmostEqual(midpoint[0], 80.14892388341609, places=8)
        self.assertAlmostEqual(midpoint[1], 0, places=8)
        self.assertAlmostEqual(great_circle(start, midpoint), great_circle(midpoint, end), places=8)
        self.assertAlmostEqual(2*great_circle(start, midpoint), great_circle(start, end), places=8)

    def test_antipodal_interpolation_is_finite_and_on_sphere(self):
        midpoint = rr.interpolate([0, 0], [0, 180], .5)
        self.assertTrue(all(np.isfinite(midpoint)))
        self.assertAlmostEqual(great_circle([0, 0], midpoint), great_circle(midpoint, [0, 180]), places=6)

    def test_profile_samples_the_geodesic_and_uses_dem_helpers(self):
        dem = object()
        with patch.object(rr.rasterio, 'open') as opened, \
             patch.object(rr, 'validate_dem') as validate, \
             patch.object(rr, 'sample_point', side_effect=lambda ds, lat, lon: lat) as elevation, \
             patch.object(rr, 'slope_at_point', return_value=2.) as slope:
            opened.return_value.__enter__.return_value = dem
            profile = rr.elevation_profile([[80, -10], [80, 10]], samples=3)
        validate.assert_called_once_with(dem)
        self.assertEqual(elevation.call_count, 3)
        self.assertEqual(slope.call_count, 3)
        self.assertAlmostEqual(profile[1]['latitude'], 80.14892, places=5)
        self.assertAlmostEqual(profile[1]['elevation_m'], 80.14892388341609, places=8)
        self.assertEqual(profile[1]['slope_degrees'], 2.)
        self.assertEqual(profile[0]['distance_km'], 0)
        self.assertAlmostEqual(profile[-1]['distance_km'], great_circle([80, -10], [80, 10]), places=2)

    def test_profile_rejects_invalid_sample_counts(self):
        for count in (0, 1, 2.5, True):
            with self.assertRaises(ValueError):
                rr.elevation_profile([[0, 0], [0, 1]], samples=count)

    def test_grid_line_endpoints(self):
        self.assertEqual(rr.grid_line((1,1),(3,3)),[(1,1),(2,2),(3,3)])

    def test_segment_refinement_avoids_hazard(self):
        grid=np.zeros((64,64),dtype=np.int8)
        grid[29:35,29:35]=3
        region={'hazard_grid':grid.tolist(),'bounds':{'north':.25,'south':-.25,'west':-.25,'east':.25}}
        with patch.object(rr,'analyze_region',return_value=region):
            result=rr.refine_segment([0,-.25],[0,.25])
        self.assertIn(result['status'],('refined','inspected'))
        self.assertEqual(result['highest_original_hazard'],3)
        self.assertEqual(result['highest_local_hazard'],0)

    def test_global_report_and_bounded_windows(self):
        fake={'status':'success','route_coordinates':[[0,0],[0,1],[0,2]],
              'direct_distance_km':118.32,'route_distance_km':118.32,
              'hazard_breakdown':{'low':3},'terrain_risk_score':0}
        with patch.object(rr,'plan',return_value=fake),patch.object(rr,'refine_segment',return_value={'status':'inspected'}),patch.object(rr,'elevation_profile',return_value=[{'elevation_m':-100},{'elevation_m':100}]):
            result=rr.refine_global_route(0,0,0,2)
        self.assertEqual(result['refinement']['sampled_windows'],2)
        self.assertEqual(result['refinement']['modified_windows'],0)
        self.assertEqual(result['scientific_report']['minimum_elevation_m'],-100)
        self.assertEqual(result['status'],'success')

    def test_failed_or_skipped_windows_do_not_overstate_coverage(self):
        fake = {'status': 'success', 'route_coordinates': [[0, i] for i in range(7)],
                'direct_distance_km': 354.948, 'route_distance_km': 354.948,
                'hazard_breakdown': {'low': 7}, 'terrain_risk_score': 0}
        checks = [{'status': 'inspected'}, {'status': 'unavailable'},
                  {'status': 'skipped_boundary'}, {'status': 'no_local_route'},
                  {'status': 'refined', 'replacement': [[0, 4.4], [0, 4.6]]},
                  {'status': 'skipped_short_segment'}]
        with patch.object(rr, 'plan', return_value=fake), \
             patch.object(rr, 'refine_segment', side_effect=checks), \
             patch.object(rr, 'elevation_profile') as profile:
            result = rr.refine_global_route(0, 0, 0, 6, include_profile=False)
        coverage = result['refinement']
        self.assertEqual(coverage['attempted_windows'], 6)
        self.assertEqual(coverage['sampled_windows'], 3)
        self.assertEqual(coverage['skipped_windows'], 2)
        self.assertEqual(coverage['unavailable_windows'], 1)
        self.assertEqual(coverage['modified_windows'], 1)
        self.assertEqual(coverage['inspected_segment_fraction'], .5)
        self.assertAlmostEqual(result['distance_increase_percent'], 0)
        self.assertEqual(result['route_distance_km'], result['refinement']['refined_route_distance_km'])
        profile.assert_not_called()

    def test_all_missing_window_is_unavailable(self):
        region = {'hazard_grid': np.full((64, 64), -1, dtype=np.int8).tolist(),
                  'bounds': {'north': .25, 'south': -.25, 'west': -.25, 'east': .25}}
        with patch.object(rr, 'analyze_region', return_value=region):
            result = rr.refine_segment([0, -.25], [0, .25])
        self.assertEqual(result['status'], 'unavailable')

    def test_comparison_same_cell_matches_mission_geometry(self):
        bounds = {'north': .25, 'south': -.25, 'west': -.25, 'east': .25}
        start, end = [.001, .001], [.001, .001001]
        summary = summarize([(31, 32)], np.zeros((64, 64), dtype=np.int8), bounds, start, end)
        self.assertEqual(summary['route_coordinates'], [start, end])

if __name__=='__main__':unittest.main()
