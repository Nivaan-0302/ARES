
from route_planner import astar_route

print("ARES — A* ALGORITHM VALIDATION")
print("--------------------------------")

# Test 1: Completely flat terrain
flat_grid = [
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0]
]

route1 = astar_route(flat_grid, (0, 0), (4, 4))

assert route1 is not None
assert route1[0] == (0, 0)
assert route1[-1] == (4, 4)
assert len(route1) == 5

print("TEST 1 PASSED: Shortest diagonal route on flat terrain")


# Test 2: A high-cost terrain barrier
hazard_grid = [
    [0, 0, 0, 0, 0],
    [0, 3, 3, 3, 0],
    [0, 3, 3, 3, 0],
    [0, 3, 3, 3, 0],
    [0, 0, 0, 0, 0]
]

route2 = astar_route(hazard_grid, (0, 0), (4, 4))

assert route2 is not None
assert route2[0] == (0, 0)
assert route2[-1] == (4, 4)
assert all(hazard_grid[r][c] != 3 for r, c in route2)

print("TEST 2 PASSED: Avoided expensive terrain")


# Test 3: Missing terrain data
blocked_grid = [
    [0, -1, 0],
    [0, -1, 0],
    [0, -1, 0]
]

route3 = astar_route(blocked_grid, (1, 0), (1, 2))

assert route3 is None

print("TEST 3 PASSED: Correctly rejected blocked route")

print("--------------------------------")
print("ALL ARES A* VALIDATION TESTS PASSED")
