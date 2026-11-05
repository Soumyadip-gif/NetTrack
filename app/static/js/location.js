document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("detectLocationButton");
    const status = document.getElementById("locationStatus");
    const latitude = document.getElementById("latitudeValue");
    const longitude = document.getElementById("longitudeValue");
    const accuracy = document.getElementById("accuracyValue");

    const searchButton = document.getElementById("findNearbySpotsButton");
    const radiusSelect = document.getElementById("nearbyRadius");
    const searchStatus = document.getElementById("nearbySpotsStatus");
    const resultsContainer = document.getElementById("nearbySpotsResults");

    if (!button || !status) return;

    let map = null;
    let marker = null;
    let accuracyCircle = null;
    let spotLayer = null;
    let currentPosition = null;

    if (typeof L !== "undefined") {
        map = L.map("locationMap").setView([20.5937, 78.9629], 5);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(map);

        spotLayer = L.layerGroup().addTo(map);
    } else {
        status.textContent = "Map library could not load. Location detection is still available.";
    }

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[character]);
    }

    function renderNearbySpots(spots) {
        if (!resultsContainer) return;

        if (!spots.length) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    No measured network locations were found within this radius.
                    New GPS-verified speed tests will help build this area’s results.
                </div>`;
            return;
        }

        resultsContainer.innerHTML = spots.map((spot, index) => `
            <article class="nearby-spot-card">
                <div class="nearby-spot-heading">
                    <strong>${index === 0 ? "Best measured spot" : `Nearby spot ${index + 1}`}</strong>
                    <span class="nearby-score">${escapeHtml(spot.score)} / 100</span>
                </div>
                <div class="nearby-spot-metrics">
                    <div><span>Download</span><strong>${escapeHtml(spot.download_mbps)} Mbps</strong></div>
                    <div><span>Upload</span><strong>${escapeHtml(spot.upload_mbps)} Mbps</strong></div>
                    <div><span>Ping</span><strong>${spot.ping_ms == null ? "N/A" : escapeHtml(spot.ping_ms) + " ms"}</strong></div>
                    <div><span>Distance</span><strong>${escapeHtml(spot.distance_km)} km</strong></div>
                </div>
                <div class="nearby-spot-footer">
                    <span>${escapeHtml(spot.test_count)} measurement(s)</span>
                    <span>Reliability: ${escapeHtml(spot.reliability)}</span>
                </div>
                <button type="button" class="nearby-map-button"
                    data-lat="${escapeHtml(spot.latitude)}"
                    data-lon="${escapeHtml(spot.longitude)}">
                    Show on map
                </button>
            </article>
        `).join("");

        resultsContainer.querySelectorAll(".nearby-map-button").forEach(mapButton => {
            mapButton.addEventListener("click", () => {
                const lat = Number(mapButton.dataset.lat);
                const lon = Number(mapButton.dataset.lon);
                if (map && Number.isFinite(lat) && Number.isFinite(lon)) {
                    map.setView([lat, lon], 17);
                }
            });
        });
    }

    async function findNearbySpots() {
        if (!currentPosition || !searchButton) return;

        const radius = radiusSelect.value;
        searchButton.disabled = true;
        searchButton.textContent = "Searching...";
        searchStatus.textContent = "Searching for real measured locations nearby...";

        try {
            const params = new URLSearchParams({
                latitude: currentPosition.latitude,
                longitude: currentPosition.longitude,
                radius_km: radius
            });

            const response = await fetch(`/api/location/best-spots?${params}`);
            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(result.message || "Nearby search failed.");
            }

            renderNearbySpots(result.data);

            if (spotLayer) {
                spotLayer.clearLayers();

                result.data.forEach((spot, index) => {
                    const point = [spot.latitude, spot.longitude];
                    L.marker(point)
                        .addTo(spotLayer)
                        .bindPopup(
                            `<strong>Nearby spot ${index + 1}</strong><br>` +
                            `Download: ${escapeHtml(spot.download_mbps)} Mbps<br>` +
                            `Ping: ${spot.ping_ms == null ? "N/A" : escapeHtml(spot.ping_ms) + " ms"}<br>` +
                            `Tests: ${escapeHtml(spot.test_count)}`
                        );
                });
            }

            searchStatus.textContent = result.message;
        } catch (error) {
            searchStatus.textContent = error.message || "Unable to search nearby locations.";
            console.error("Nearby spot search failed:", error);
        } finally {
            searchButton.disabled = false;
            searchButton.textContent = "Find Best Nearby Spots";
        }
    }

    if (searchButton) {
        searchButton.addEventListener("click", findNearbySpots);
    }

    button.addEventListener("click", () => {
        if (!navigator.geolocation) {
            status.textContent = "Geolocation is not supported by this browser.";
            return;
        }

        button.disabled = true;
        button.textContent = "Detecting...";
        status.textContent = "Requesting location permission...";

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const accuracyMeters = position.coords.accuracy;

                currentPosition = {
                    latitude: lat,
                    longitude: lon,
                    accuracy: accuracyMeters
                };

                latitude.textContent = lat.toFixed(6);
                longitude.textContent = lon.toFixed(6);
                accuracy.textContent = `${Math.round(accuracyMeters)} metres`;
                status.textContent = "Your location was detected successfully.";

                if (map) {
                    const point = [lat, lon];
                    map.setView(point, 15);

                    if (marker) map.removeLayer(marker);
                    if (accuracyCircle) map.removeLayer(accuracyCircle);

                    marker = L.marker(point)
                        .addTo(map)
                        .bindPopup("Your current location")
                        .openPopup();

                    accuracyCircle = L.circle(point, {
                        radius: accuracyMeters,
                        color: "#3b82f6",
                        fillOpacity: 0.12
                    }).addTo(map);
                }

                if (searchButton) {
                    searchButton.disabled = false;
                }

                button.disabled = false;
                button.textContent = "Detect My Location";
                searchStatus.textContent = "GPS ready. Search for measured locations within 3 km.";
            },
            (error) => {
                const messages = {
                    1: "Location permission denied. Allow location access in your browser settings.",
                    2: "Your location is currently unavailable. Check GPS or device location settings.",
                    3: "Location request timed out. Please try again."
                };

                status.textContent = messages[error.code] || "Unable to detect your location.";
                button.disabled = false;
                button.textContent = "Try Again";
            },
            {
                enableHighAccuracy: true,
                timeout: 20000,
                maximumAge: 30000
            }
        );
    });
});
