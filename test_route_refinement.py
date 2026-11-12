"""Tests of bounded route refinement, independent of the 2 GB DEM."""
import unittest
from unittest.mock import patch
import numpy as np
import route_refinement as rr


class RefinementTests(unittest.TestCase):
    def test_dateline_interpolation(self):
        p=rr.interpolate([0,179],[0,-179],.5)
        self.assertAlmostEqual(abs(p[1]),180)

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

if __name__=='__main__':unittest.main()
