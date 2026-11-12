"""Fast global-routing tests without loading the 2GB MOLA raster."""
import numpy as np
import global_navigation as nav

nav.global_model = lambda: (np.zeros((nav.HEIGHT,nav.WIDTH)),np.zeros((nav.HEIGHT,nav.WIDTH),dtype=np.int8))
for coords in [(0,0,0,10),(0,179,0,-179),(80,-120,-70,75),(0,0,0,0)]:
    result = nav.plan(*coords)
    assert result['status'] == 'success', result
    assert result['route_coordinates'][0] == list(coords[:2])
    assert result['route_coordinates'][-1] == list(coords[2:])
    assert result['route_distance_km'] >= result['direct_distance_km']
    print('PASS',coords,'distance',result['route_distance_km'],'km')
print('GLOBAL ROUTING SYNTHETIC TESTS PASSED')
