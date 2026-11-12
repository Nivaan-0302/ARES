
from terrain_region import analyze_region
import numpy as np

print("ARES — REGIONAL TERRAIN HAZARD TEST")
print("-----------------------------------")

# Test a region near the Martian equator


result = analyze_region(
    latitude=-35.7,
    longitude=-36.3,
    radius_degrees=0.25
)



grid = np.array(result["hazard_grid"])


print("Region centre: -35.7° latitude, -36.3° longitude")
print("Grid dimensions:", result["shape"])
print("Total pixels:", grid.size)
print()


labels = {
    -1: "NO DATA",
    0: "LOW",
    1: "MODERATE",
    2: "HIGH",
    3: "EXTREME"
}

for value, label in labels.items():
    count = int(np.sum(grid == value))
    percentage = 100 * count / grid.size

    print(f"{label}: {count} pixels ({percentage:.2f}%)")

print("-----------------------------------")
print("Regional terrain analysis complete.")
