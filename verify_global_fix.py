"""Safe regression: synthetic low-hazard grid, without opening the MOLA raster."""
import numpy as np
import global_navigation as g

original = g.global_model
try:
    hazards = np.zeros((g.HEIGHT, g.WIDTH), dtype=np.int8)
    g.global_model = lambda: (np.zeros_like(hazards, dtype=np.float32), hazards)
    for start, end in [((0,179),(0,-179)), ((0,0),(0,90)), ((10,179.8),(10,-179.8)), ((0,0),(0,0))]:
        r = g.plan(*start, *end)
        assert r['status'] == 'success', r
        assert r['route_coordinates'][0] == list(start)
        assert r['route_coordinates'][-1] == list(end)
        assert r['route_distance_km'] + .002 >= r['direct_distance_km']
        print(f'{start} -> {end}: direct={r["direct_distance_km"]:.3f} km; route={r["route_distance_km"]:.3f} km; waypoints={r["waypoint_count"]}')
        if start == (0,179):
            assert r['route_distance_km'] < 125, 'Artificial endpoint detour persists'
    print('PASS: Global endpoint geometry regression tests')
finally:
    g.global_model = original
