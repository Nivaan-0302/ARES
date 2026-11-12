"""Optional regional MOLA route comparison. Never modifies the mission route."""
import heapq
import math
import numpy as np
from terrain_region import analyze_region
from route_planner import (astar_route, coordinates_to_grid, grid_route_to_coordinates,
                           calculate_route_distance, mars_cell_distance_km)
from global_navigation import great_circle
from mission_routing import validate_coordinates

LABELS = ('low','moderate','high','extreme')
COSTS = (1.,3.,8.,20.)

def shortest_path(grid, start, goal, bounds):
    rows, cols = grid.shape
    def valid(cell):
        r,c=cell
        return 0<=r<rows and 0<=c<cols and 0<=int(grid[r,c])<=3
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

def summarize(cells,grid,bounds,start,end):
    centres=grid_route_to_coordinates(cells,bounds,grid.shape)
    coords=[list(start),list(end)] if start==end else [list(start)]+centres+[list(end)]
    counts={name:sum(int(grid[r,c])==i for r,c in cells) for i,name in enumerate(LABELS)}
    distance=calculate_route_distance(coords)
    weighted=sum(mars_cell_distance_km(a,b,bounds,grid.shape)*COSTS[int(grid[b])]
                 for a,b in zip(cells,cells[1:]))
    return {'route_coordinates':coords,'route_distance_km':round(distance,3),
            'hazard_breakdown':counts,'high_extreme_cells':counts['high']+counts['extreme'],
            'path_cells':len(cells),'weighted_grid_cost_km':round(weighted,3)}

def compare(a,b,c,d):
    a,b,c,d=validate_coordinates((a,b,c,d))
    start,end=(a,b),(c,d)
    if abs(a-c)>.24 or abs((b-d+180)%360-180)>.24 or abs(a)>=89.7 or abs(b)>=179.7:
        return {'status':'not_comparable','reason':'Comparison is limited to endpoints within one regional 0.5-degree MOLA window. Global routes use a different planning scale.'}
    region=analyze_region(a,b)
    grid=np.asarray(region['hazard_grid'],dtype=np.int8)
    bounds=region['bounds']
    s=coordinates_to_grid(*start,bounds,grid.shape)
    g=coordinates_to_grid(*end,bounds,grid.shape)
    if s is None or g is None:
        return {'status':'not_comparable','reason':'Destination is outside the regional analysis window.'}
    distance=shortest_path(grid,s,g,bounds)
    weighted=astar_route(grid,s,g,bounds=bounds)
    if not distance or not weighted:
        return {'status':'no_route','reason':'No valid path on the regional MOLA grid.'}
    dsum=summarize(distance,grid,bounds,start,end)
    wsum=summarize(weighted,grid,bounds,start,end)
    return {'status':'success','scope':'Regional 0.5-degree MOLA hazard grid',
            'start':[a,b],'destination':[c,d],
            'distance_optimized':dsum,'terrain_weighted':wsum,
            'comparison':{'distance_difference_km':round(wsum['route_distance_km']-dsum['route_distance_km'],3),
                          'high_extreme_cells_avoided':dsum['high_extreme_cells']-wsum['high_extreme_cells'],
                          'weighted_cost_improvement_percent':round(100*(dsum['weighted_grid_cost_km']-wsum['weighted_grid_cost_km'])/dsum['weighted_grid_cost_km'],2) if dsum['weighted_grid_cost_km'] else 0},
            'limitations':'Both paths use the same regional DEM-scale grid. Hazard classes are slope heuristics; weighted cost is not travel time, energy consumption, or rover failure probability. Endpoints connect to cell centres and route distance includes these connectors.'}
