"""Synthetic geometry/masking regressions; no external DEM or downloads."""
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from dem_data import (DEMValidationError, validate_dem, validate_global_coverage, geographic_to_dataset,
                      dataset_to_geographic, pixel_spacing_metres, read_elevation,
                      sample_point, slope_at_point, classify_slopes)

try:
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin
except ModuleNotFoundError:
    rasterio = None


class FakeCRS:
    def __init__(self, projected=False, a=3389500., b=None):
        self.is_geographic = not projected
        self.params = {'proj':'eqc' if projected else 'longlat', 'a':a,
                       'b':a if b is None else b}
        if projected:
            self.params.update(units='m',lat_ts=30,lat_0=0,lon_0=0,x_0=120,y_0=-50)
    def to_dict(self): return self.params.copy()
    def to_string(self): return 'synthetic Mars CRS'
    def to_wkt(self): return 'GEOGCS["Mars",SPHEROID["Mars",3389500,0],UNIT["degree",0.0174532925199433]]'


class FakeDEM:
    def __init__(self, projected=False):
        self.crs=FakeCRS(projected)
        self.count=1; self.width=self.height=5
        self.scales=(1.,); self.offsets=(0.,); self.units=('m',)
        self.transform=SimpleNamespace(a=1.,b=0.,c=-2.5,d=0.,e=-1.,f=2.5)
        self.bounds=SimpleNamespace(left=-2.5,right=2.5,bottom=-2.5,top=2.5)
        self.array=np.ma.array(np.zeros((5,5)),mask=np.zeros((5,5),dtype=bool))
    def read(self,band,**kwargs):
        window=kwargs.get('window')
        if window is None: return self.array.copy()
        (r0,r1),(c0,c1)=window
        return self.array[r0:r1,c0:c1].copy()
    def index(self,x,y):
        return math.floor((y-self.transform.f)/self.transform.e), math.floor((x-self.transform.c)/self.transform.a)


class TerrainProcessingTests(unittest.TestCase):
    def test_missing_center_and_derivative_support_remain_unknown(self):
        z=np.zeros((5,5)); z[2,2]=np.nan
        _,hazard=classify_slopes(z,463.,463.)
        for cell in ((2,2),(1,2),(3,2),(2,1),(2,3)):
            self.assertEqual(hazard[cell],-1)
        self.assertEqual(hazard[0,0],0)

    def test_global_polar_support_and_longitude_wrap(self):
        z=np.zeros((5,5)); z[1,2]=np.nan; z[3,3]=np.nan
        _,hazard=classify_slopes(z,100.,100.,wrap_longitude=True)
        self.assertEqual(hazard[0,2],-1)
        self.assertEqual(hazard[-1,3],-1)
        z=np.zeros((5,5)); z[2,-1]=np.nan
        _,hazard=classify_slopes(z,100.,100.,wrap_longitude=True)
        self.assertEqual(hazard[2,0],-1)

    def test_per_row_spacing_changes_classification(self):
        z=np.tile([0.,10.,20.],(3,1))
        slopes,hazards=classify_slopes(z,np.array([100.,50.,10.]),100.)
        self.assertAlmostEqual(slopes[0,1],math.degrees(math.atan(.1)))
        self.assertAlmostEqual(slopes[-1,1],45.)
        self.assertEqual(hazards[0,1],1)
        self.assertEqual(hazards[-1,1],3)

    def test_threshold_boundaries_are_consistent(self):
        for angle,expected in ((5.,0),(15.,1),(25.,2),(30.,3)):
            z=np.tile(np.arange(3)*math.tan(math.radians(angle)),(3,1))
            _,hazard=classify_slopes(z,1.,1.)
            self.assertEqual(int(hazard[1,1]),expected)

    def test_rejects_earth_rotated_and_unsupported_crs(self):
        ds=FakeDEM(); ds.crs=FakeCRS(a=6378137.)
        with self.assertRaises(DEMValidationError):validate_dem(ds)
        ds=FakeDEM(); ds.transform.b=.1
        with self.assertRaises(DEMValidationError):validate_dem(ds)
        ds=FakeDEM(projected=True); ds.crs.params['proj']='merc'
        with self.assertRaises(DEMValidationError):validate_dem(ds)
        ds=FakeDEM(projected=True); ds.crs.params['b']=3376200.
        with self.assertRaises(DEMValidationError):validate_dem(ds)

    def test_geographic_domain_and_spacing(self):
        ds=FakeDEM();ds.bounds.left=0.;ds.bounds.right=360.
        self.assertEqual(geographic_to_dataset(ds,-10.,20.),(350.,20.))
        dx,dy=pixel_spacing_metres(ds,60.)
        self.assertAlmostEqual(dx/dy,.5)

    def test_dateline_wrap_only_for_full_world_coverage(self):
        ds=FakeDEM();ds.bounds.left=-180.;ds.bounds.right=180.
        self.assertEqual(geographic_to_dataset(ds,180.,0.),(-180.,0.))
        ds.bounds.left=-10.;ds.bounds.right=10.
        self.assertEqual(geographic_to_dataset(ds,10.,0.),(10.,0.))

    def test_global_coverage_rejects_partial_and_noncanonical_extents(self):
        metadata=validate_dem(FakeDEM())
        with self.assertRaises(DEMValidationError):validate_global_coverage(metadata)
        metadata['geographic_bounds']={'west':-180.,'east':180.,'south':-90.,'north':90.}
        validate_global_coverage(metadata)
        metadata['geographic_bounds']['west']=-179.
        metadata['geographic_bounds']['east']=181.
        with self.assertRaises(DEMValidationError):validate_global_coverage(metadata)

    def test_projected_transform_round_trip(self):
        ds=FakeDEM(projected=True)
        x,y=geographic_to_dataset(ds,1.,1.)
        lon,lat=dataset_to_geographic(ds,x,y)
        self.assertAlmostEqual(lon,1.);self.assertAlmostEqual(lat,1.)
        self.assertAlmostEqual(x,120+3389500*math.radians(1)*math.cos(math.radians(30)))
        dx,dy=pixel_spacing_metres(ds,60.)
        self.assertAlmostEqual(dx/dy,math.cos(math.radians(60))/math.cos(math.radians(30)))

    def test_scales_offsets_and_masks(self):
        ds=FakeDEM();ds.scales=(2.,);ds.offsets=(100.,)
        ds.array[:]=2.;ds.array.mask[1,1]=True
        arr=read_elevation(ds)
        self.assertEqual(float(arr[2,2]),104.)
        self.assertTrue(np.ma.is_masked(arr[1,1]))
        self.assertEqual(sample_point(ds,0.,0.),104.)
        ds.array.mask[2,2]=True
        self.assertIsNone(sample_point(ds,0.,0.))
        self.assertIsNone(slope_at_point(ds,0.,0.))
        self.assertIsNone(sample_point(ds,10.,0.))

    def test_unknown_units_are_disclosed_instead_of_fabricated(self):
        ds=FakeDEM();ds.units=(None,)
        self.assertTrue(validate_dem(ds)['elevation_units_assumed'])
        ds.units=('feet',)
        with self.assertRaises(DEMValidationError):validate_dem(ds)

    @unittest.skipUnless(rasterio is not None,'Rasterio is not installed')
    def test_clipped_raster_bounds_match_returned_grid(self):
        import terrain_region
        crs=rasterio.crs.CRS.from_proj4('+proj=longlat +a=3389500 +b=3389500 +no_defs')
        with MemoryFile() as memory:
            with memory.open(driver='GTiff',height=50,width=50,count=1,dtype='float32',
                             crs=crs,transform=from_origin(-2.5,2.5,.1,.1),nodata=-9999.) as ds:
                ds.write(np.zeros((50,50),dtype=np.float32),1)
            with patch.object(terrain_region.rasterio,'open',side_effect=lambda _:memory.open()):
                region=terrain_region.analyze_region(0.,2.4)
                self.assertAlmostEqual(region['bounds']['east'],2.5)
                self.assertEqual(region['shape'][1],round((region['bounds']['east']-region['bounds']['west'])/.1))
                self.assertTrue(region['terrain_metadata']['window_clipped_to_dataset'])
                with self.assertRaises(ValueError):terrain_region.analyze_region(0.,0.,radius_degrees=.001)


if __name__=='__main__':
    unittest.main()
