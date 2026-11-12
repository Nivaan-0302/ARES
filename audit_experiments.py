"""Non-destructive ARES global geometry and hazard-avoidance diagnostic.
Run from the ARES folder: python3 audit_experiments.py
Uses synthetic grids; does not access or change the MOLA raster.
"""
import math
import heapq
import numpy as np
import global_navigation as g
from route_planner import astar_route


def global_case():
    original = g.global_model
    try:
        hazards = np.zeros((g.HEIGHT, g.WIDTH), dtype=np.int8)
        g.global_model = lambda: (np.zeros_like(hazards, dtype=np.float32), hazards)
        result = g.plan(0, 179, 0, -179)
        coords = result['route_coordinates']
        legs = [g.great_circle(a,b) for a,b in zip(coords, coords[1:])]
        print('EXPERIMENT 07: uniform LOW-hazard global grid (no terrain penalties)')
        print('  Direct great-circle distance: %.3f km' % g.great_circle((0,179),(0,-179)))
        print('  ARES route distance:          %.3f km' % result['route_distance_km'])
        print('  Endpoint connector distances: %.3f + %.3f km' % (legs[0], legs[-1]))
        print('  Grid-centre path distance:    %.3f km' % sum(legs[1:-1]))
        print('  Waypoints:                   ',len(coords))
        print('  Grid route points:           ',coords[1:-1])
        print('  Interpretation: if this reproduces ~202 km, excess length is caused by coarse grid geometry, not hazards.')
    finally:
        g.global_model = original


def count_hazards(path, grid):
    return {name:sum(grid[r,c] == idx for r,c in path) for idx,name in enumerate(('low','moderate','high','extreme'))}


def shortest_path(grid, start, goal):
    rows, cols = grid.shape
    frontier = [(0.0,start)]
    best={start:0.0}
    previous={}
    while frontier:
        cost,cur=heapq.heappop(frontier)
        if cost > best.get(cur,math.inf)+1e-9: continue
        if cur==goal:
            path=[cur]
            while path[-1] in previous: path.append(previous[path[-1]])
            return path[::-1]
        r,c=cur
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if not dr and not dc:continue
                nr,nc=r+dr,c+dc
                if not (0<=nr<rows and 0<=nc<cols) or grid[nr,nc]<0:continue
                if dr and dc and (grid[r,nc]<0 or grid[nr,c]<0):continue
                neighbor=(nr,nc)
                step=math.hypot(dr,dc)
                if cost+step < best.get(neighbor,math.inf):
                    best[neighbor]=cost+step
                    previous[neighbor]=cur
                    heapq.heappush(frontier,(cost+step,neighbor))
    return None


def local_case():
    grid=np.zeros((9,13),dtype=np.int8)
    grid[3:6,4:9]=3
    start=(4,0);goal=(4,12)
    shortest=shortest_path(grid,start,goal)
    weighted=astar_route(grid,start,goal)
    print('\nEXPERIMENT 08: controlled 9x13 grid, extreme hazard block')
    for name,path in [('Distance-only baseline',shortest),('Terrain-weighted A*',weighted)]:
        length=sum(math.dist(a,b) for a,b in zip(path,path[1:]))
        counts=count_hazards(path,grid)
        print('  %-23s length=%6.3f cells=%2d hazards=%s' % (name,length,len(path),counts))
    print('  Note: synthetic evidence only; real Hale Crater comparison still needs a separate MOLA-backed run.')
    assert count_hazards(weighted,grid)['extreme'] == 0
    assert count_hazards(shortest,grid)['extreme'] > 0
    print('  PASS: terrain-weighted route avoids the synthetic extreme hazard region.')

if __name__=='__main__':
    global_case()
    local_case()
