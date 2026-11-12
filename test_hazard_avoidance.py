
from route_planner import astar_route

print("ARES — HAZARD AVOIDANCE VALIDATION")
print("--------------------------------")

# A direct route crosses high-cost terrain.
# A longer low-hazard route exists around it.
grid = [
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 3, 3, 3, 0, 0],
    [0, 0, 3, 3, 3, 0, 0],
    [0, 0, 3, 3, 3, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0]
]

start = (3, 0)
goal = (3, 6)

route = astar_route(grid, start, goal)

print("Calculated route:", route)

assert route is not None
assert route[0] == start
assert route[-1] == goal

extreme_cells = [
    (r, c) for r, c in route
    if grid[r][c] == 3
]

assert len(extreme_cells) == 0, (
    "ARES crossed extreme-hazard terrain!"
)

print("Extreme-hazard cells crossed:", len(extreme_cells))
print("TEST PASSED: ARES avoided extreme-hazard terrain")


print("\nARES — TERRAIN RISK SCORE VALIDATION")
print("--------------------------------")

test_hazards = {
    "low": 5,
    "moderate": 3,
    "high": 2,
    "extreme": 0
}

weights = {
    "low": 0,
    "moderate": 1,
    "high": 3,
    "extreme": 6
}

total_waypoints = sum(test_hazards.values())

weighted_risk = sum(
    test_hazards[level] * weight
    for level, weight in weights.items()
)

risk_score = round(
    weighted_risk / (total_waypoints * 6) * 100,
    2
)

print("Terrain risk score:", risk_score)

assert risk_score == 15.0

print("TEST PASSED: Terrain risk score calculation is correct")
