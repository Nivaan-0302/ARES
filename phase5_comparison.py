"""Optional regional MOLA route comparison. Never modifies the mission route."""
import heapq
import math
import numpy as np
from terrain_region import analyze_region
from route_planner import (astar_route, coordinates_to_grid, grid_route_with_endpoints,
                           calculate_route_distance, mars_cell_distance_km,
                           hazard_cell_mask, TERRAIN_COSTS)
from global_navigation import great_circle
from mission_routing import validate_coordinates

LABELS = ('low','moderate','high','extreme')
COSTS = TERRAIN_COSTS

def shortest_path(grid, start, goal, bounds):
    grid = np.asarray(grid)
    if grid.ndim != 2 or min(grid.shape) == 0:
        raise ValueError('A hazard grid must be a nonempty two-dimensional array.')
    rows, cols = grid.shape
    available = hazard_cell_mask(grid)
    def valid(cell):
        r,c=cell
        return (isinstance(r,(int,np.integer)) and isinstance(c,(int,np.integer))
                and 0<=r<rows and 0<=c<cols and available[r,c])
    if not valid(start) or not valid(goal): return None
    frontier=[(0.,start)]
    best={start:0.}
    parent={}
    while frontier:
        cost,cell=heapq.heappop(frontier)
        if cost>best[cell]+1e-10: continue
        if cell==goal:
            path=[cell]
            while cell in parent:
                cell=parent[cell];path.append(cell)
            return path[::-1]
        r,c=cell
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr==dc==0:continue
                nxt=(r+dr,c+dc)
                if not valid(nxt):continue
                if dr and dc and (not valid((r+dr,c)) or not valid((r,c+dc))):continue
                distance=mars_cell_distance_km(cell,nxt,bounds,grid.shape)
                new=cost+distance
                if new+1e-10<best.get(nxt,float('inf')):
                    best[nxt]=new;parent[nxt]=cell
                    heapq.heappush(frontier,(new,nxt))
    return None

def summarize(cells,grid,bounds,start,end, *, round_metrics=True):
    coords=grid_route_with_endpoints(cells,bounds,grid.shape,start,end)
    counts={name:sum(int(grid[r,c])==i for r,c in cells) for i,name in enumerate(LABELS)}
    distance=calculate_route_distance(coords,round_digits=None)
    weighted=sum(mars_cell_distance_km(a,b,bounds,grid.shape)*COSTS[int(grid[b])]
                 for a,b in zip(cells,cells[1:]))
    return {'route_coordinates':coords,'route_distance_km':round(distance,3) if round_metrics else distance,
            'hazard_breakdown':counts,'high_extreme_cells':counts['high']+counts['extreme'],
            'path_cells':len(cells),'weighted_grid_cost_km':round(weighted,3) if round_metrics else weighted}

def compare(a,b,c,d):
    a,b,c,d=validate_coordinates((a,b,c,d))
    start,end=(a,b),(c,d)
    if abs(a-c)>.24 or abs((b-d+180)%360-180)>.24 or abs(a)>=89.7 or abs(b)>=179.7:
        return {'status':'not_comparable','reason':'Comparison is limited to endpoints within one regional 0.5-degree MOLA window. Global routes use a different planning scale.'}
    region=analyze_region(a,b)
    grid=np.asarray(region['hazard_grid'])
    bounds=region['bounds']
    s=coordinates_to_grid(*start,bounds,grid.shape)
    g=coordinates_to_grid(*end,bounds,grid.shape)
    if s is None or g is None:
        return {'status':'not_comparable','reason':'Destination is outside the regional analysis window.'}
    distance=shortest_path(grid,s,g,bounds)
    weighted=astar_route(grid,s,g,bounds=bounds)
    if not distance or not weighted:
        return {'status':'no_route','reason':'No valid path on the regional MOLA grid.'}
    dsum=summarize(distance,grid,bounds,start,end,round_metrics=False)
    wsum=summarize(weighted,grid,bounds,start,end,round_metrics=False)
    comparison={'distance_difference_km':round(wsum['route_distance_km']-dsum['route_distance_km'],3),
                'high_extreme_cells_avoided':dsum['high_extreme_cells']-wsum['high_extreme_cells'],
                'weighted_cost_improvement_percent':round(100*(dsum['weighted_grid_cost_km']-wsum['weighted_grid_cost_km'])/dsum['weighted_grid_cost_km'],2) if dsum['weighted_grid_cost_km'] else 0}
    for summary in (dsum, wsum):
        for metric in ('route_distance_km', 'weighted_grid_cost_km'):
            summary[metric]=round(summary[metric],3)
    return {'status':'success','scope':'Regional 0.5-degree MOLA hazard grid',
            'start':[a,b],'destination':[c,d],
            'distance_optimized':dsum,'terrain_weighted':wsum,
            'comparison':comparison,
            'limitations':'Both paths use the same regional DEM-scale grid. Hazard classes are slope heuristics; weighted cost is not travel time, energy consumption, or rover failure probability. Multi-cell routes include endpoint-to-centre connectors; same-cell routes connect the requested endpoints directly. Grid cost excludes endpoint connectors.'}
