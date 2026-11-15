"""Regional Flask endpoint regressions at the native 4 ppd footprint."""
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import rasterio
from rasterio.transform import from_origin

import terrain_region
from terrain_api import app


class RegionalReferenceTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def region(self, path, lat, lon):
        with patch.object(terrain_region, 'DEM_PATH', path):
            response = self.client.get('/api/terrain-region', query_string={'lat': lat, 'lon': lon})
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def test_native_seam_and_missing_derivative_support(self):
        # Synthetic ridge with a missing axial neighbour for the second row.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'edge.tif'
            z = np.tile(np.arange(1440, dtype='int16') * 4, (720, 1))
            z[359, 2] = 6000
            z[360, 2] = -32768
            with rasterio.open(path, 'w', driver='GTiff', width=1440, height=720,
                               count=1, dtype='int16', nodata=-32768,
                               crs='+proj=longlat +R=3396000',
                               transform=from_origin(0, 90, .25, .25)) as dataset:
                dataset.write(z, 1)
                dataset.units = ('m',)
            result = self.region(path, 0, 0)
            self.assertEqual(result['shape'], [2, 2])
            self.assertEqual(result['bounds'], {'west': 0., 'east': .5, 'south': -.25, 'north': .25})
            self.assertEqual(result['elevation_grid'], [[0., 4.], [0., 4.]])
            self.assertEqual(result['hazard_grid'], [[-1, 1], [-1, -1]])
            self.assertTrue(result['terrain_metadata']['window_clipped_to_dataset'])
            polar = self.region(path, 90, 0)
            self.assertEqual(polar['bounds'], {'west': 0., 'east': .5, 'south': 89.5, 'north': 90.})
            self.assertEqual(polar['hazard_grid'], [[-1, -1], [-1, 0]])
            western = self.region(path, 0, -.125)
            self.assertEqual((western['bounds']['west'], western['bounds']['east']), (-.5, 0.))
            self.assertEqual(western['hazard_grid'], [[0, -1], [0, -1]])
            with patch.object(terrain_region, 'DEM_PATH', path):
                maximum = terrain_region.analyze_region(0, 0, radius_degrees=.5)
                self.assertEqual(maximum['shape'], [4, 2])
                with self.assertRaisesRegex(ValueError, 'at most 0.5 degrees'):
                    terrain_region.analyze_region(0, 0, radius_degrees=.51)

    def test_real_pds_reference(self):
        path = os.environ.get('ARES_GLOBAL_REFERENCE_PATH')
        if not path:
            self.skipTest('Set ARES_GLOBAL_REFERENCE_PATH to the native PDS 4 ppd reference')
        result = self.region(path, 0, 0)
        self.assertEqual(result['shape'], [2, 2])
        self.assertEqual(result['bounds'], {'west': 0., 'east': .5, 'south': -.25, 'north': .25})
        spacing = 3396000 * math.radians(.25)
        self.assertAlmostEqual(result['terrain_metadata']['pixel_height_m'], spacing)
        self.assertAlmostEqual(result['terrain_metadata']['pixel_width_range_m'][0],
                               spacing * math.cos(math.radians(.125)))
        with rasterio.open(path) as dataset:
            native = dataset.read(1, window=((358, 362), (0, 3))).astype(float)
        self.assertEqual(result['elevation_grid'], native[1:3, :2].tolist())
        self.assertEqual(result['elevation_grid'][1][0], -1495.)
        dx = spacing * math.cos(math.radians(.125))
        for row in (1, 2):
            slope = math.degrees(math.atan(math.hypot(
                (native[row, 2] - native[row, 0]) / (2 * dx),
                (native[row + 1, 1] - native[row - 1, 1]) / (2 * spacing))))
            expected = sum(slope > threshold for threshold in (5, 15, 25))
            self.assertEqual(result['hazard_grid'][row - 1], [-1, expected])
