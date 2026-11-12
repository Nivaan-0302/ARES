"""ARES Experiment 10: compare distance-only and hazard-weighted routes on real MOLA.
Read-only: does not change application files or the DEM.
"""
import heapq
import math
from collections import Counter
import numpy as np
from terrain_region import analyze_region
from route_planner import astar_route, coordinates_to_grid, mars_cell_distance_km

COSTS = {0: 1.0, 1: 3.0, 2: 8.0, 3: 20.0}
NAMES = {0: 'LOW', 1: 'MODERATE', 2: 'HIGH', 3: 'EXTREME'}
DIRECTIONS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

def distance_only(grid, start, goal, bounds):
    rows, cols = grid.shape
    def valid(p):
        r,c=p
        return 0<=r<rows and 0<=c<cols and int(grid[r,c]) in COSTS
    if not valid(start) or not valid(goal):
        return None
    heap=[(0.0,start)]
    best={start:0.0}
    parents={}
    while heap:
        dist,cell=heapq.heappop(heap)
        if dist>best.get(cell,math.inf)+1e-10: continue
        if cell==goal:
            route=[cell]
            while cell in parents:
                cell=parents[cell]
                route.append(cell)
            return route[::-1]
        for dr,dc in DIRECTIONS:
            nxt=(cell[0]+dr,cell[1]+dc)
            if not valid(nxt): continue
            if dr and dc and (not valid((cell[0]+dr,cell[1])) or not valid((cell[0],cell[1]+dc))):
                continue
            nd=dist+mars_cell_distance_km(cell,nxt,bounds,grid.shape)
            if nd+1e-10<best.get(nxt,math.inf):
                best[nxt]=nd
                parents[nxt]=cell
                heapq.heappush(heap,(nd,nxt))
    return None

def metrics(grid,route,bounds):
    if route is None: return None
    counts=Counter(int(grid[p]) for p in route)
    length=0.0
    weighted=0.0
    for a,b in zip(route,route[1:]):
        d=mars_cell_distance_km(a,b,bounds,grid.shape)
        length+=d
        weighted+=d*COSTS[int(grid[b])]
    return {'km':length,'weighted_km':weighted,'counts':counts,'hazard_cells':sum(counts[k] for k in (1,2,3)),'high_extreme':sum(counts[k] for k in (2,3))}

def print_metrics(label,metric):
    if metric is None:
        print(f'  {label}: NO ROUTE')
        return
    c=metric['counts']
    print(f"  {label}: length={metric['km']:.3f} km; weighted cost={metric['weighted_km']:.3f} cost-km")
    print('    cells: '+', '.join(f'{NAMES[k]}={c[k]}' for k in range(4)))

def compare(grid,bounds,a,b,heading):
    start=coordinates_to_grid(*a,bounds,grid.shape)
    goal=coordinates_to_grid(*b,bounds,grid.shape)
    print(f'\n{heading}: {a} -> {b}')
    print(f'  start cell={start}; goal cell={goal}')
    if start is None or goal is None:
        print('  SKIP: endpoint outside the 64x64 region')
        return None
    baseline=distance_only(grid,start,goal,bounds)
    weighted=astar_route(grid,start,goal,bounds=bounds)
    bm=metrics(grid,baseline,bounds)
    wm=metrics(grid,weighted,bounds)
    print_metrics('Distance-only A*',bm)
    print_metrics('Terrain-weighted A*',wm)
    if bm is None or wm is None:
        print('  INCONCLUSIVE: route unavailable')
        return None
    if wm['weighted_km']>bm['weighted_km']+1e-6:
        print('  WARNING: weighted A* cost is higher than baseline; investigate algorithm')
    if wm['hazard_cells']<bm['hazard_cells']:
        print('  OBSERVED: weighted route encounters fewer non-LOW cells')
    elif wm['hazard_cells']==bm['hazard_cells']:
        print('  OBSERVED: equal non-LOW cell counts (compare weighted cost and hazard severity)')
    else:
        print('  OBSERVED: weighted route encounters more non-LOW cells (severity may differ)')
    return bm,wm

def main():
    print('ARES EXPERIMENT 10 — REAL MOLA HALE CRATER AUDIT')
    print('Reading actual DEM; no application files are modified.')
    region=analyze_region(-35.7,-36.3,radius_degrees=0.25)
    grid=np.asarray(region['hazard_grid'],dtype=np.int8)
    bounds=region['bounds']
    print('Grid shape:',grid.shape)
    print('Hazard distribution:',{NAMES[k]:int(np.sum(grid==k)) for k in range(4)})
    print('No-data cells:',int(np.sum(grid==-1)))
    compare(grid,bounds,(-35.75,-36.40),(-35.65,-36.20),'PRIMARY: previous Hale Crater test')
    # Deterministic additional routes to see whether the algorithm responds to actual hazards.
    tests=[((-35.90,-36.50),(-35.50,-36.10)),
           ((-35.90,-36.10),(-35.50,-36.50)),
           ((-35.80,-36.45),(-35.60,-36.15)),
           ((-35.85,-36.20),(-35.55,-36.35)),
           ((-35.65,-36.50),(-35.75,-36.10))]
    improvements=0
    for i,(a,b) in enumerate(tests,1):
        result=compare(grid,bounds,a,b,f'ADDITIONAL {i}')
        if result and result[1]['hazard_cells']<result[0]['hazard_cells']:
            improvements+=1
    print('\nSUMMARY: additional pairs with fewer non-LOW cells:',improvements,'/',len(tests))
    print('Interpretation: hazard avoidance is evidenced only where the weighted path reduces exposure or weighted cost versus the baseline.')
    print('NOTE: slope classes and costs are illustrative, not certified rover safety limits.')

if __name__=='__main__':
    main()
