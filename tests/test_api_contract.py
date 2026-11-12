"""Flask API security/response regressions; skipped when runtime deps are absent.

Tests use the Flask test client and mocked terrain access. They do not open or
modify the original MOLA raster and do not start a network listener.
"""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
RUNTIME_AVAILABLE = all(importlib.util.find_spec(name) is not None
                        for name in ('flask', 'rasterio', 'numpy'))
if RUNTIME_AVAILABLE:
    import terrain_api as api


@unittest.skipUnless(RUNTIME_AVAILABLE, 'Flask and Rasterio runtime dependencies are required')
class APIContractTests(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()

    def test_public_interface_is_served(self):
        for path in ('/', '/index.html', '/mission_state.js', '/style.css'):
            with self.subTest(path=path):
                with self.client.get(path) as response:
                    self.assertEqual(response.status_code, 200)

    def test_backend_and_private_paths_are_not_public_assets(self):
        for path in ('/terrain_api.py', '/AGENTS.md', '/README.md', '/.env',
                     '/requirements.txt', '/data/mola128_mola64_merge_90Nto90S_SimpleC_clon0.tif',
                     '/vendor/../terrain_api.py', '/vendor/%2e%2e/AGENTS.md'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_liveness_does_not_open_the_dataset(self):
        with patch.object(api.rasterio, 'open') as opened:
            response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['status'], 'ok')
        opened.assert_not_called()

    def test_readiness_fails_cleanly_without_dataset(self):
        with patch.object(api.rasterio, 'open', side_effect=OSError('/private/path/dem.tif missing')):
            response = self.client.get('/readyz')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()['status'], 'not_ready')
        self.assertNotIn('/private/path', response.get_data(as_text=True))

    def test_readiness_returns_validated_metadata(self):
        metadata = {'width': 360, 'height': 180, 'elevation_units': 'metres',
                    'geographic_bounds': {'west': -180., 'east': 180.,
                                          'south': -90., 'north': 90.}}
        with patch.object(api.rasterio, 'open'), patch.object(api, 'validate_dem', return_value=metadata):
            response = self.client.get('/readyz')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ready', 'dataset': metadata})

    def test_readiness_rejects_partial_raster_for_global_features(self):
        metadata = {'width': 360, 'height': 180, 'elevation_units': 'metres',
                    'geographic_bounds': {'west': -10., 'east': 10.,
                                          'south': -10., 'north': 10.}}
        # Exercise the real global-coverage helper after generic raster validation.
        with patch.object(api.rasterio, 'open'), patch.object(api, 'validate_dem', return_value=metadata):
            response = self.client.get('/readyz')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()['status'], 'not_ready')

    def test_invalid_coordinates_are_rejected_before_terrain_work(self):
        endpoints = ('/api/route', '/api/mission-route', '/api/global-route',
                     '/api/refined-route', '/api/route-comparison')
        with patch.object(api.rasterio, 'open') as opened, patch.object(api, 'analyze_region') as region:
            for endpoint in endpoints:
                for bad in ('nan', 'inf', '91', '-91', 'invalid'):
                    with self.subTest(endpoint=endpoint, value=bad):
                        response = self.client.get(endpoint, query_string={
                            'start_lat': bad, 'start_lon': '0', 'end_lat': '0', 'end_lon': '1'})
                        self.assertEqual(response.status_code, 400)
                        self.assertIsInstance(response.get_json(), dict)
            for endpoint in ('/api/elevation', '/api/slope', '/api/terrain-region'):
                with self.subTest(endpoint=endpoint):
                    response = self.client.get(endpoint, query_string={'lat': '0', 'lon': 'nan'})
                    self.assertEqual(response.status_code, 400)
                    self.assertIsInstance(response.get_json(), dict)
        opened.assert_not_called()
        region.assert_not_called()

    def test_missing_coordinates_return_json_errors(self):
        for endpoint in ('/api/elevation', '/api/slope', '/api/terrain-region',
                         '/api/mission-route', '/api/global-route', '/api/refined-route',
                         '/api/route', '/api/route-comparison'):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.get_json(), dict)

    def test_busy_server_returns_retryable_response(self):
        slots = MagicMock()
        slots.acquire.return_value = False
        with patch.object(api, '_analysis_slots', slots), patch.object(api.rasterio, 'open') as opened:
            response = self.client.get('/api/global-relief')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()['status'], 'busy')
        self.assertEqual(response.headers['Retry-After'], '1')
        opened.assert_not_called()
        slots.release.assert_not_called()

    def test_busy_analysis_does_not_block_health(self):
        slots = MagicMock()
        slots.acquire.return_value = False
        with patch.object(api, '_analysis_slots', slots):
            response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        slots.acquire.assert_not_called()

    def test_analysis_slot_is_released_after_success_and_failure(self):
        import global_navigation
        for failure in (False, True):
            slots = MagicMock()
            slots.acquire.return_value = True
            with self.subTest(failure=failure), patch.object(api, '_analysis_slots', slots):
                with patch.object(global_navigation, 'relief',
                                  side_effect=OSError('synthetic read failure') if failure else None,
                                  return_value={'source': 'synthetic test fixture'}):
                    response = self.client.get('/api/global-relief')
            self.assertEqual(response.status_code, 500 if failure else 200)
            self.assertIsInstance(response.get_json(), dict)
            slots.release.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
