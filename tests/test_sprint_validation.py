"""Real Rasterio/Flask regressions and explicitly synthetic MemoryFile fixtures.

Set ARES_SAMPLE_PATH to the provided mola_sample_256.tif. No dataset is bundled.
"""
import hashlib
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds, from_origin

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dem_data as dem
import global_navigation as global_nav
import terrain_region as regional
import terrain_api as api
import mission_routing as mission
import route_refinement as refinement
from route_planner import astar_route, coordinates_to_grid

MARS='GEOGCS["Mars",DATUM["Mars",SPHEROID["Mars",3396190,169.894447223612]],PRIMEM["Reference_Meridian",0],UNIT["degree",0.0174532925199433]]'
SAMPLE=os.environ.get('ARES_SAMPLE_PATH')
GLOBAL_REFERENCE=os.environ.get('ARES_GLOBAL_REFERENCE_PATH')


class BoundaryAndMissingDataTests(unittest.TestCase):
    def test_pixel_edges_and_equivalent_longitudes(self):
        bounds=dict(west=-1.,east=1.,south=-1.,north=1.)
        self.assertEqual(coordinates_to_grid(1.,-1.,bounds,(256,256)),(0,0))
        for lat,lon in ((1.,1.),(-1.,-1.),(-1.,1.)):
            self.assertIsNone(coordinates_to_grid(lat,lon,bounds,(256,256)))
        self.assertEqual(coordinates_to_grid(0.,360.,bounds,(256,256)),(128,128))
        self.assertEqual(global_nav.cell_for(0.,180.),global_nav.cell_for(0.,-180.))

    def test_unknown_codes_are_never_truncated_into_traversable_classes(self):
        for value in (np.nan,np.inf,-1.,.5,2.9,4.,None):
            with self.subTest(value=value):
                self.assertIsNone(astar_route([[0,value,0]],(0,0),(0,2)))

    def test_polar_direct_shortcut_does_not_skip_unknown_coarse_cells(self):
        hazard=np.zeros((180,360),dtype=np.int8);hazard[0,181]=-1
        with patch.object(global_nav,'global_model',return_value=(np.zeros_like(hazard),hazard)):
            result=global_nav.plan(89.9,-80.,89.9,80.)
        self.assertEqual(result['status'],'success')
        self.assertGreater(len(result['route_coordinates']),2)

    def test_owner_reported_full_extent_accepts_registration_not_partial_data(self):
        metadata=dict(width=46081,height=23041,geographic_bounds=dict(
            west=-180.,east=179.99609389834364,south=-90.0019530720196,north=90.))
        coverage=dem.validate_global_coverage(metadata)
        self.assertEqual(coverage['canonical_west'],-180.)
        self.assertAlmostEqual(coverage['edge_offsets_degrees']['east'],-.00390610165636)
        metadata['geographic_bounds']['east']=179.9
        with self.assertRaises(dem.DEMValidationError):dem.validate_global_coverage(metadata)

    def test_verified_usgs_projected_header_extent_is_supported(self):
        from types import SimpleNamespace
        from affine import Affine
        from rasterio.crs import CRS
        ds=SimpleNamespace(count=1,width=46081,height=23041,scales=(1.,),offsets=(0.,),units=(None,),
            crs=CRS.from_user_input('ESRI:103885'),
            transform=Affine(463.0836,0,-10669677.095995119,0,-463.08359999999993,5334954.318897561),
            bounds=SimpleNamespace(left=-10669677.095995119,bottom=-5334954.908702438,
                                   right=10669678.27560488,top=5334954.318897561))
        meta=dem.validate_dem(ds)
        dem.validate_global_coverage(meta)
        self.assertEqual(dem.geographic_to_dataset(ds,180.,0.),dem.geographic_to_dataset(ds,-180.,0.))

    def test_actual_rasterio_mask_and_shared_point_regional_stencil(self):
        z=np.zeros((9,9),dtype=np.int16);z[4,4]=-32768
        with MemoryFile() as mem:
            with mem.open(driver='GTiff',height=9,width=9,count=1,dtype='int16',
                          crs=MARS,transform=from_origin(-.45,.45,.1,.1),nodata=-32768) as ds:
                ds.write(z,1)
            with rasterio.open(mem.name) as ds:
                self.assertIsNone(dem.sample_point(ds,0.,0.))
                for r in range(1,8):
                    for c in range(1,8):
                        lon,lat=ds.xy(r,c)
                        value=dem.slope_at_point(ds,lat,lon)
                        invalid=abs(r-4)+abs(c-4)<=1
                        self.assertEqual(value is None,invalid)
            with patch.object(regional,'DEM_PATH',mem.name):
                region=regional.analyze_region(0.,0.,radius_degrees=.25)
            grid=np.asarray(region['hazard_grid'])
            self.assertEqual(int(np.count_nonzero(grid==-1)),5)
            self.assertTrue(np.all(np.isin(grid,[-1,0])))

    def test_read_only_metadata_cache_cannot_be_changed_by_a_caller(self):
        with MemoryFile() as mem:
            with mem.open(driver='GTiff',height=3,width=3,count=1,dtype='int16',
                          crs=MARS,transform=from_origin(-1.,1.,.5,.5)) as writer:
                writer.write(np.zeros((3,3),dtype=np.int16),1)
            with rasterio.open(mem.name) as ds:
                first=dem.validate_dem(ds)
                first['geographic_bounds']['west']=500.;first['radius_m']=1.
                second=dem.validate_dem(ds)
                self.assertEqual(second['geographic_bounds']['west'],-1.)
                self.assertGreater(second['radius_m'],3300000.)

    def test_canonical_global_warp_does_not_stretch_offset_bounds(self):
        z=np.zeros((36,72),dtype=np.int16);z[:,36:]=1000
        bounds=(-180.,-90.0019530720196,179.99609389834364,90.)
        with MemoryFile() as mem:
            with mem.open(driver='GTiff',height=36,width=72,count=1,dtype='int16',
                          crs=MARS,transform=from_bounds(*bounds,72,36),nodata=-32768) as ds:
                ds.write(z,1)
            heights,hazards=global_nav._cached_global_model((mem.name,0,0))
            native_boundary=(bounds[0]+bounds[2])/2
            expected=1000*(0-native_boundary)  # overlap fraction in canonical [-1,0] degree cell
            self.assertAlmostEqual(float(heights[90,179]),expected,places=5)
            self.assertEqual(float(heights[90,180]),1000.)
            self.assertEqual(hazards.shape,(180,360))


@unittest.skipUnless(SAMPLE and Path(SAMPLE).is_file(),'Set ARES_SAMPLE_PATH to the supplied real 256-pixel sample')
class RealSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=Path(SAMPLE)
        cls.original_hash=hashlib.sha256(cls.path.read_bytes()).hexdigest()
        if cls.original_hash!='c99f92579062c39934295690bd0a0644d3e73a60a1c7fbf14c93d714d6198981':
            raise unittest.SkipTest('This numerical reference is for the specifically supplied 256x256 sample')
        with rasterio.open(cls.path) as ds:
            cls.z=ds.read(1,masked=True);cls.transform=ds.transform
            cls.metadata=dem.validate_dem(ds)

    def tearDown(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),self.original_hash)

    def test_actual_metadata_and_raw_values(self):
        self.assertEqual(self.z.shape,(256,256))
        self.assertEqual(self.z.dtype,np.dtype('int16'))
        self.assertEqual(int(np.ma.getmaskarray(self.z).sum()),0)
        self.assertEqual((int(self.z.min()),int(self.z.max())),(-1558,-960))
        self.assertTrue(self.metadata['elevation_units_assumed'])

    def test_exhaustive_pixel_indexing_and_point_lookups(self):
        with rasterio.open(self.path) as ds:
            for r in range(256):
                for c in range(256):
                    lon,lat=ds.xy(r,c)
                    if dem.sample_point(ds,lat,lon)!=float(self.z[r,c]):
                        self.fail(f'Incorrect value at row {r}, column {c}')
            self.assertEqual(dem.sample_point(ds,0.,0.),-1517.)
            self.assertIsNone(dem.sample_point(ds,ds.bounds.top,ds.bounds.right))

    def test_independent_surface_normals_and_hazard_counts(self):
        z=np.asarray(self.z,dtype=float);t=self.transform;radius=self.metadata['radius_m']
        lat=t.f+(np.arange(256)+.5)*t.e
        dx=radius*math.radians(t.a)*np.cos(np.radians(lat));dy=radius*math.radians(-t.e)
        u=np.zeros((254,254,3));v=np.zeros_like(u)
        u[:,:,0]=2*dx[1:-1,None];u[:,:,2]=z[1:-1,2:]-z[1:-1,:-2]
        v[:,:,1]=2*dy;v[:,:,2]=z[2:,1:-1]-z[:-2,1:-1]
        normal=np.cross(u,v)
        reference=np.degrees(np.arctan2(np.linalg.norm(normal[:,:,:2],axis=2),normal[:,:,2]))
        slopes,hazards=dem.classify_slopes(self.z,dx,dy)
        np.testing.assert_allclose(slopes[1:-1,1:-1],reference,rtol=0,atol=1e-10)
        expected=np.select([reference<=5,reference<=15,reference<=25],[0,1,2],default=3)
        np.testing.assert_array_equal(hazards[1:-1,1:-1],expected)
        self.assertEqual(int(np.count_nonzero(expected==1)),150)

    def test_real_flask_terrain_routing_comparison_and_readiness(self):
        targets=[api,regional,dem,mission,refinement,global_nav]
        patches=[patch.object(module,'DEM_PATH',self.path) for module in targets if hasattr(module,'DEM_PATH')]
        for manager in patches:manager.start()
        try:
            client=api.app.test_client()
            self.assertEqual(client.get('/healthz').status_code,200)
            self.assertEqual(client.get('/readyz').status_code,503) # partial sample is not a full planet
            elev=client.get('/api/elevation?lat=0&lon=0')
            self.assertEqual(elev.status_code,200);self.assertEqual(elev.json['elevation_m'],-1517.)
            slope=client.get('/api/slope?lat=0&lon=0')
            self.assertEqual(slope.status_code,200);self.assertEqual(slope.json['slope_degrees'],.777)
            region=client.get('/api/terrain-region?lat=0&lon=0')
            self.assertEqual(region.status_code,200);self.assertEqual(region.json['shape'],[64,64])
            query='?start_lat=0&start_lon=0&end_lat=.1&end_lon=.1'
            for endpoint in ('/api/route','/api/mission-route'):
                result=client.get(endpoint+query)
                self.assertEqual(result.status_code,200,result.json)
                self.assertEqual(result.json['route_coordinates'][0],[0.,0.])
                self.assertEqual(result.json['route_coordinates'][-1],[.1,.1])
                self.assertEqual(result.json['hazard_breakdown']['extreme'],0)
            comparison=client.get('/api/route-comparison'+query)
            self.assertEqual(comparison.status_code,200,comparison.json)
            self.assertEqual(comparison.json['status'],'success')
            self.assertGreaterEqual(comparison.json['comparison']['weighted_cost_improvement_percent'],-1e-8)
        finally:
            for manager in reversed(patches):manager.stop()


@unittest.skipUnless(GLOBAL_REFERENCE and Path(GLOBAL_REFERENCE).is_file(),
                    'Set ARES_GLOBAL_REFERENCE_PATH to the separately prepared PDS4ppd global reference')
class RealGlobalReferenceTests(unittest.TestCase):
    def setUp(self):
        self.path=Path(GLOBAL_REFERENCE)
        self.managers=[patch.object(module,'DEM_PATH',self.path)
            for module in (api,regional,dem,mission,refinement,global_nav) if hasattr(module,'DEM_PATH')]
        for manager in self.managers:manager.start()
        global_nav.global_model.cache_clear()

    def tearDown(self):
        global_nav.global_model.cache_clear()
        for manager in reversed(self.managers):manager.stop()

    def test_real_global_model_and_full_readiness(self):
        elevation,hazard=global_nav.global_model()
        self.assertEqual(elevation.shape,(180,360));self.assertTrue(np.isfinite(elevation).all())
        self.assertTrue(np.isin(hazard,[-1,0,1,2,3]).all())
        result=api.app.test_client().get('/readyz')
        self.assertEqual(result.status_code,200,result.json)

    def test_real_global_dateline_and_high_latitude_routes(self):
        for coords in ((0.,179.,0.,-179.),(85.,170.,85.,-170.)):
            with self.subTest(coords=coords):
                result=global_nav.plan(*coords)
                self.assertEqual(result['status'],'success',result)
                self.assertEqual(result['route_coordinates'][0],list(coords[:2]))
                self.assertEqual(result['route_coordinates'][-1],list(coords[2:]))
                self.assertGreaterEqual(result['route_distance_km']+.001,result['direct_distance_km'])

    def test_real_flask_mission_refinement_and_profile(self):
        result=api.app.test_client().get('/api/mission-route?start_lat=10&start_lon=10&end_lat=11&end_lon=11')
        self.assertEqual(result.status_code,200,result.json)
        self.assertEqual(result.json['status'],'success')
        report=result.json['scientific_report']
        self.assertEqual(report['elevation_sample_count'],25)
        ref=result.json['refinement']
        self.assertEqual(ref['attempted_windows'],ref['sampled_windows']+ref['skipped_windows']+ref['unavailable_windows'])


if __name__=='__main__':unittest.main()
