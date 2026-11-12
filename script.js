/* ARES — Mars Terrain Explorer and Mission Selection */

// Initialize the Mars map
const marsMap = L.map("mars-map", {
    crs: L.CRS.EPSG4326,
    center: [0, 0],
    zoom: 1,
    minZoom: 0,
    maxZoom: 6,
    worldCopyJump: false,
    attributionControl: true
});

// NASA Mars Trek imagery
const marsImagery = L.tileLayer(
    "https://trek.nasa.gov/tiles/Mars/EQ/Mars_Viking_MDIM21_ClrMosaic_global_232m/1.0.0/default/default028mm/{z}/{y}/{x}.jpg",
    {
        tileSize: 256,
        minZoom: 0,
        maxZoom: 6,
        noWrap: true,
        bounds: [[-90, -180], [90, 180]],
        attribution: "Mars Viking MDIM21 imagery: NASA Mars Trek"
    }
);

marsImagery.addTo(marsMap);
marsMap.setMaxBounds([[-90, -180], [90, 180]]);

/* ARES — Regional Terrain Hazard Overlay */

// Separate layer for displaying MOLA-derived terrain hazards
const hazardOverlay = L.layerGroup().addTo(marsMap);
const autonomousRouteLayer = L.layerGroup().addTo(marsMap);

// Colors represent illustrative terrain-steepness categories
const hazardColors = {
    0: "#22c55e",  // LOW — green
    1: "#facc15",  // MODERATE — yellow
    2: "#f97316",  // HIGH — orange
    3: "#ef4444"   // EXTREME — red
};

console.log("ARES hazard overlay initialized");


// Selected mission locations
let landingSite = null;
let destination = null;
let landingMarker = null;
let destinationMarker = null;
let routeLine = null;

// Used to prevent old API requests from updating new missions
let missionVersion = 0;

// Approximate mean radius of Mars, in kilometres
const MARS_RADIUS_KM = 3389.5;

// Calculate great-circle distance on Mars
function marsDistance(pointA, pointB) {
    const toRadians = degrees => degrees * Math.PI / 180;

    const lat1 = toRadians(pointA.lat);
    const lat2 = toRadians(pointB.lat);
    const deltaLat = toRadians(pointB.lat - pointA.lat);
    const deltaLon = toRadians(pointB.lng - pointA.lng);

    const a =
        Math.sin(deltaLat / 2) ** 2 +
        Math.cos(lat1) * Math.cos(lat2) *
        Math.sin(deltaLon / 2) ** 2;

    const c = 2 * Math.atan2(
        Math.sqrt(a),
        Math.sqrt(Math.max(0, 1 - a))
    );

    return MARS_RADIUS_KM * c;
}

// Retrieve real NASA MOLA elevation
async function getMarsElevation(latitude, longitude) {
    try {
        const response = await fetch(
            `/api/elevation?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`
        );

        if (!response.ok) {
            throw new Error("Elevation data unavailable");
        }

        const data = await response.json();
        return data.elevation_m;

    } catch (error) {
        console.error("ARES elevation error:", error);
        return null;
    }
}

// Create popup text
function locationPopup(title, point, elevationText, extraText = "") {
    return (
        "<b>" + title + "</b><br>" +
        "Latitude: " + point.lat.toFixed(4) + "°<br>" +
        "Longitude: " + point.lng.toFixed(4) + "°<br>" +
        "MOLA elevation: " + elevationText +
        extraText
    );
}

// Load elevation into a marker popup

async function updateMarkerElevation(
    marker,
    point,
    title,
    extraText,
    version
) {
    // Request NASA MOLA elevation and slope
    const [elevation, terrain] = await Promise.all([
        getMarsElevation(point.lat, point.lng),
        getMarsSlope(point.lat, point.lng)
    ]);

    const slope = terrain?.slope ?? null;
    const hazard = terrain?.hazard ?? null;

    // Ignore old requests from previous missions
    if (version !== missionVersion || !marsMap.hasLayer(marker)) {
        return;
    }

    const elevationText =
        elevation === null
            ? "Unavailable"
            : elevation.toLocaleString() + " m";

    const slopeText =
        slope === null
            ? "Unavailable"
            : slope.toFixed(3) + "°";

    marker.setPopupContent(
        locationPopup(
            title,
            point,
            elevationText,
            
"<br>Estimated terrain slope: " + slopeText +
"<br>Terrain steepness: " + (hazard ?? "Unavailable") +
extraText

        )
    );


    // Update the Mission Overview terrain card
    const terrainStatus = document.getElementById("terrain-status");
    const terrainDetails = document.getElementById("terrain-details");
    const terrainElevation = document.getElementById("terrain-elevation");
    const terrainSlope = document.getElementById("terrain-slope");
    const terrainHazard = document.getElementById("terrain-hazard");


    if (
        terrainStatus &&
        terrainDetails &&
        terrainElevation &&
        terrainSlope
    ) {
        const hasData = elevation !== null && slope !== null;

        terrainStatus.textContent = hasData
            ? "DATA AVAILABLE"
            : "DATA UNAVAILABLE";

        terrainDetails.hidden = !hasData;

        if (hasData) {
            terrainElevation.textContent =
                "Elevation: " + elevationText;

            terrainSlope.textContent =
                "Estimated slope: " + slopeText;
            
            terrainHazard.textContent =
                "Terrain steepness: " + (hazard ?? "Unavailable");

        }
    }


}

// 2D map selections update the same mission shown on the 3D globe.
marsMap.on('click', event => {
    window.ARESMission.selectPointSafely({lat: event.latlng.lat, lon: event.latlng.lng});
});
let displayedLandingKey = null;
function synchronize2D(event) {
    const {start, end, route} = event.detail;
    missionVersion++;
    if (landingMarker) marsMap.removeLayer(landingMarker);
    if (destinationMarker) marsMap.removeLayer(destinationMarker);
    if (routeLine) marsMap.removeLayer(routeLine);
    landingMarker = destinationMarker = routeLine = null;
    autonomousRouteLayer.clearLayers();
    landingSite = start ? L.latLng(start.lat, start.lon) : null;
    destination = end ? L.latLng(end.lat, end.lon) : null;
    const key = start ? `${start.lat.toFixed(6)},${start.lon.toFixed(6)}` : null;
    if (key !== displayedLandingKey) {
        displayedLandingKey = key;
        hazardOverlay.clearLayers();
        if (start) displayTerrainHazards(start.lat, start.lon);
    }
    if (start) landingMarker = L.marker([start.lat, start.lon]).addTo(marsMap)
        .bindPopup(locationPopup('ARES Landing Site', landingSite, 'See terrain telemetry'));
    if (end) destinationMarker = L.marker([end.lat, end.lon]).addTo(marsMap)
        .bindPopup(locationPopup('ARES Destination', destination, 'See terrain telemetry'));
    if (route && Array.isArray(route) && route.length > 1) {
        // Split across the antimeridian to avoid drawing a false planet-wide chord.
        let segment = [];
        for (const point of route) {
            if (segment.length && Math.abs(point[1] - segment[segment.length - 1][1]) > 180) {
                if (segment.length > 1) L.polyline(segment, {color:'#00e5ff',weight:4}).addTo(autonomousRouteLayer);
                segment = [];
            }
            segment.push(point);
        }
        if (segment.length > 1) L.polyline(segment, {color:'#00e5ff',weight:4}).addTo(autonomousRouteLayer);
    } // No straight-line substitute while a terrain-aware route is calculating.
}
window.addEventListener('ares:mission', synchronize2D);
console.log("ARES mission selection and MOLA elevation system initialized");


/* ARES — NASA MOLA Slope Integration */


async function getMarsSlope(latitude, longitude) {
    try {
        const response = await fetch(
            `/api/slope?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`
        );

        if (!response.ok) {
            throw new Error("Terrain analysis unavailable");
        }

        const data = await response.json();

        return {
            slope: data.slope_degrees,
            hazard: data.hazard_level
        };

    } catch (error) {
        console.error("ARES terrain analysis error:", error);
        return null;
    }
}

/* ARES — Regional Hazard Map Renderer */

async function displayTerrainHazards(latitude, longitude) {
    try {
        console.log("ARES: Loading regional terrain hazards...");

        const response = await fetch(
            `/api/terrain-region?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`
        );

        if (!response.ok) {
            throw new Error("Regional terrain data unavailable");
        }

        const data = await response.json();

        const grid = data.hazard_grid;
        const bounds = data.bounds;

        const rows = grid.length;
        const cols = grid[0].length;

        const latitudeStep = (bounds.north - bounds.south) / rows;
        const longitudeStep = (bounds.east - bounds.west) / cols;

        // Clear any previous hazard visualization
        hazardOverlay.clearLayers();

        // Use one canvas-backed overlay for efficient rendering
        const canvas = document.createElement("canvas");
        canvas.width = cols;
        canvas.height = rows;

        const context = canvas.getContext("2d");
        const image = context.createImageData(cols, rows);

        const rgbColors = {
            0: [34, 197, 94],
            1: [250, 204, 21],
            2: [249, 115, 22],
            3: [239, 68, 68]
        };

        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                const hazard = grid[row][col];
                const color = rgbColors[hazard];

                const index = (row * cols + col) * 4;

                if (!color) {
                    image.data[index + 3] = 0;
                    continue;
                }

                image.data[index] = color[0];
                image.data[index + 1] = color[1];
                image.data[index + 2] = color[2];
                image.data[index + 3] = 150;
            }
        }

        context.putImageData(image, 0, 0);

        const overlayBounds = [
            [bounds.south, bounds.west],
            [bounds.north, bounds.east]
        ];

        L.imageOverlay(
            canvas.toDataURL("image/png"),
            overlayBounds,
            {
                opacity: 0.8,
                interactive: false
            }
        ).addTo(hazardOverlay);

        console.log(
            `ARES: Rendered ${rows * cols} terrain hazard cells`
        );

        marsMap.fitBounds(overlayBounds, {
            padding: [40, 40],
            maxZoom: 6
        });


    } catch (error) {
        console.error("ARES hazard map error:", error);
    }
}



async function displayAutonomousRoute(start, end) {
    const version = missionVersion;

    try {
        console.log("ARES: Calculating A* route...");

        const params = new URLSearchParams({
            start_lat: start.lat,
            start_lon: start.lng,
            end_lat: end.lat,
            end_lon: end.lng
        });

        const response = await fetch(`/api/route?${params}`);
        const data = await response.json();

        // Ignore results from an older mission
        if (version !== missionVersion) return;

        autonomousRouteLayer.clearLayers();

        if (data.status === "outside_region") {
            console.log(
                "ARES: Destination outside regional terrain coverage."
            );
            return;
        }

        if (!response.ok || data.status !== "success") {
            throw new Error(
                data.message || data.error || "Route unavailable"
            );
        }

        const path = L.polyline(data.route_coordinates, {
            color: "#00e5ff",
            weight: 4,
            opacity: 0.95
        }).addTo(autonomousRouteLayer);

        
    path.bindPopup(`
    <strong>ARES Autonomous Route</strong>
    <hr>
    <strong>Algorithm:</strong> A*
    <br><strong>Terrain Source:</strong> NASA MOLA
    <br><strong>Waypoints:</strong> ${data.waypoint_count}
    <br><strong>A* Route Distance:</strong> ${data.route_distance_km.toFixed(3)} km
    <br><strong>Direct Distance:</strong> ${data.direct_distance_km.toFixed(3)} km
    <br><strong>Distance Difference:</strong> ${data.extra_distance_km.toFixed(3)} km
    <br><strong>Difference:</strong> ${data.distance_increase_percent.toFixed(2)}%
    <br><strong>Route Efficiency:</strong> ${data.route_efficiency_percent.toFixed(2)}%
    <hr>
    <strong>Terrain Risk Score:</strong> ${data.terrain_risk_score.toFixed(2)} / 100
    <br><small>Illustrative DEM-scale relative risk index</small>
    <hr>
    <strong>Terrain Hazard Breakdown</strong>
    <br>🟢 Low: ${data.hazard_breakdown.low} waypoints
    <br>🟡 Moderate: ${data.hazard_breakdown.moderate} waypoints
    <br>🟠 High: ${data.hazard_breakdown.high} waypoints
    <br>🔴 Extreme: ${data.hazard_breakdown.extreme} waypoints
    <hr>
    <small>Regional DEM-scale route. Distances are preliminary.</small>
`);

    
        // Update the Route Planner dashboard card
        const routeStatus = document.getElementById("route-status");
        const routeDetails = document.getElementById("route-details");
        const routeDistance = document.getElementById("route-distance");
        const routeEfficiency = document.getElementById("route-efficiency");
        const routeRisk = document.getElementById("route-risk");
        const routeWaypoints = document.getElementById("route-waypoints");

        if (
            routeStatus &&
            routeDetails &&
            routeDistance &&
            routeEfficiency &&
            routeRisk &&
            routeWaypoints
        ) {
            routeStatus.textContent = "ROUTE CALCULATED";
            routeDetails.hidden = false;

            routeDistance.textContent =
                "Distance: " + data.route_distance_km.toFixed(3) + " km";

            routeEfficiency.textContent =
                "Efficiency: " + data.route_efficiency_percent.toFixed(2) + "%";

            routeRisk.textContent =
                "Terrain risk: " + data.terrain_risk_score.toFixed(2) + " / 100";

            routeWaypoints.textContent =
                "Waypoints: " + data.waypoint_count;
        }

        console.log(
            `ARES: Route calculated with ${data.waypoint_count} waypoints`
        );

    } catch (error) {
        if (version === missionVersion) {
            console.error("ARES routing error:", error);
        }
    }
}
