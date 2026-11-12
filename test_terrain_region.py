"""Optional real-MOLA integration checks; explicitly skipped without the DEM."""
from pathlib import Path
import unittest
import numpy as np
from dem_data import DEM_PATH


@unittest.skipUnless(Path(DEM_PATH).is_file(), "NASA MOLA DEM is not supplied; set ARES_DEM_PATH")
class RealTerrainRegionTests(unittest.TestCase):
    def test_hale_region_has_valid_classifications(self):
        from terrain_region import analyze_region
        result = analyze_region(-35.7, -36.3, radius_degrees=.25)
        grid = np.asarray(result["hazard_grid"])
        self.assertEqual(grid.ndim, 2)
        self.assertEqual(list(grid.shape), result["shape"])
        self.assertTrue(all(size >= 2 for size in grid.shape))
        self.assertTrue(np.isin(grid, [-1, 0, 1, 2, 3]).all())
        self.assertTrue((grid >= 0).any(), "Real DEM has no usable samples in the selected region")
        bounds = result["bounds"]
        self.assertLess(bounds["south"], -35.7)
        self.assertGreater(bounds["north"], -35.7)
        self.assertLess(bounds["west"], -36.3)
        self.assertGreater(bounds["east"], -36.3)


if __name__ == "__main__":
    unittest.main()
