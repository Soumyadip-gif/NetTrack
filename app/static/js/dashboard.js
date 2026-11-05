
const API = {
    stats: "/api/network/stats",
    history: "/api/network/history",
    status: "/api/network/status",
    wifi: "/api/network/wifi"
};

const REFRESH_INTERVAL = 5000;
const MAX_CHART_POINTS = 30;

const elements = {
    download: document.getElementById("downloadSpeed"),
    upload: document.getElementById("uploadSpeed"),
    activeInterfaces: document.getElementById("activeInterfaces"),
    totalMeasurements: document.getElementById("totalMeasurements"),
    interfaceTable: document.getElementById("interfaceTable"),
    workerStatus: document.getElementById("workerStatus"),
    workerDot: document.getElementById("workerDot"),
    lastUpdated: document.getElementById("lastUpdated"),
    wifiNetworkCount: document.getElementById("wifiNetworkCount"),
    wifiAccessPointCount: document.getElementById("wifiAccessPointCount"),
    wifiScanStatus: document.getElementById("wifiScanStatus"),
    wifiNetworkTable: document.getElementById("wifiNetworkTable"),
    scanWifiButton: document.getElementById("scanWifiButton")
};

let trafficChart = null;
let chartInitialized = false;
let lastHistoryId = null;

function formatSpeed(value) {
    return Number(value || 0).toFixed(3);
}

function formatTimestamp(timestamp) {
    if (!timestamp) return "Not available";

    const date = new Date(timestamp);

    return Number.isNaN(date.getTime())
        ? "Not available"
        : date.toLocaleTimeString();
}

function initializeChart() {
    const canvas = document.getElementById("trafficChart");

    if (!canvas || typeof Chart === "undefined") {
        console.error("Chart.js is unavailable.");
        return;
    }

    trafficChart = new Chart(canvas, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "Download",
                    data: [],
                    borderColor: "#58a6ff",
                    backgroundColor: "rgba(88, 166, 255, 0.10)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 2
                },
                {
                    label: "Upload",
                    data: [],
                    borderColor: "#35d39a",
                    backgroundColor: "rgba(53, 211, 154, 0.08)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 300
            },
            interaction: {
                intersect: false,
                mode: "index"
            },
            plugins: {
                legend: {
                    labels: {
                        color: "#a8b5c9",
                        usePointStyle: true,
                        boxWidth: 7
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: "rgba(148, 163, 184, 0.08)"
                    },
                    ticks: {
                        color: "#8492a9",
                        maxTicksLimit: 8
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: "rgba(148, 163, 184, 0.08)"
                    },
                    ticks: {
                        color: "#8492a9"
                    },
                    title: {
                        display: true,
                        text: "Mbps",
                        color: "#8492a9"
                    }
                }
            }
        }
    });

    chartInitialized = true;
}

async function fetchJSON(url) {
    const response = await fetch(url, {
        cache: "no-store"
    });

    if (!response.ok) {
        throw new Error(`Request failed: ${url} (${response.status})`);
    }

    return response.json();
}

async function updateNetworkStats() {
    try {
        const response = await fetchJSON(API.stats);

        if (!response.success) {
            throw new Error("Network statistics unavailable.");
        }

        const interfaces = response.data.interfaces || [];

        const active = interfaces.filter(item =>
            item.is_up &&
            !item.interface.toLowerCase().includes("loopback")
        );

        const download = active.reduce(
            (sum, item) => sum + Number(item.download_mbps || 0),
            0
        );

        const upload = active.reduce(
            (sum, item) => sum + Number(item.upload_mbps || 0),
            0
        );

        elements.download.textContent = formatSpeed(download);
        elements.upload.textContent = formatSpeed(upload);
        elements.activeInterfaces.textContent = active.length;

        renderInterfaces(interfaces);

        elements.lastUpdated.textContent =
            `Last updated: ${new Date().toLocaleTimeString()}`;

    } catch (error) {
        console.error("Stats update failed:", error);
    }
}

function renderInterfaces(interfaces) {
    if (!interfaces.length) {
        elements.interfaceTable.innerHTML =
            `<tr><td colspan="6" class="empty-state">No interfaces detected.</td></tr>`;
        return;
    }

    elements.interfaceTable.innerHTML = interfaces.map(item => {
        const isUp = Boolean(item.is_up);

        const ipAddresses = (item.ip_addresses || []).join(", ") || "—";

        return `
            <tr>
                <td>${escapeHTML(item.interface)}</td>
                <td>
                    <span class="interface-status">
                        <span class="status-dot ${isUp ? "" : "offline"}"></span>
                        ${isUp ? "Up" : "Down"}
                    </span>
                </td>
                <td>${escapeHTML(ipAddresses)}</td>
                <td>${Number(item.speed_mbps || 0)} Mbps</td>
                <td>${formatSpeed(item.download_mbps)} Mbps</td>
                <td>${formatSpeed(item.upload_mbps)} Mbps</td>
            </tr>
        `;
    }).join("");
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

async function updateNetworkStatus() {
    try {
        const response = await fetchJSON(API.status);

        if (!response.success) {
            throw new Error("Monitoring status unavailable.");
        }

        const data = response.data;

        elements.workerStatus.textContent =
            data.running ? "Monitoring active" : "Monitoring stopped";

        elements.workerDot.classList.toggle("offline", !data.running);

        elements.totalMeasurements.textContent =
            Number(data.total_measurements || 0).toLocaleString();

    } catch (error) {
        elements.workerStatus.textContent = "Status unavailable";
        elements.workerDot.classList.add("offline");
        console.error("Status update failed:", error);
    }
}

async function updateTrafficHistory() {
    if (!chartInitialized) return;

    try {
        const response = await fetchJSON(API.history);

        if (!response.success) {
            throw new Error("Traffic history unavailable.");
        }

        const records = [...(response.data || [])]
            .filter(record =>
                Number.isFinite(Number(record.download_mbps)) &&
                Number.isFinite(Number(record.upload_mbps))
            )
            .reverse();

        // Use only newly stored records to avoid repeating chart points.
        const newRecords = lastHistoryId === null
            ? records.slice(-MAX_CHART_POINTS)
            : records.filter(record => record.id > lastHistoryId);

        newRecords.forEach(record => {
            trafficChart.data.labels.push(
                formatTimestamp(record.timestamp)
            );

            trafficChart.data.datasets[0].data.push(
                Number(record.download_mbps)
            );

            trafficChart.data.datasets[1].data.push(
                Number(record.upload_mbps)
            );
        });

        if (records.length) {
            lastHistoryId = Math.max(
                lastHistoryId || 0,
                ...records.map(record => Number(record.id))
            );
        }

        while (trafficChart.data.labels.length > MAX_CHART_POINTS) {
            trafficChart.data.labels.shift();
            trafficChart.data.datasets.forEach(dataset => {
                dataset.data.shift();
            });
        }

        trafficChart.update("none");

    } catch (error) {
        console.error("History update failed:", error);
    }
}


async function updateWifiNetworks() {
    if (!elements.wifiNetworkTable) return;

    elements.wifiScanStatus.textContent = "Scanning nearby networks...";

    try {
        const response = await fetchJSON(API.wifi);

        if (!response.success) {
            throw new Error("Wi-Fi scan unavailable.");
        }

        const data = response.data;
        const networks = data.networks || [];

        elements.wifiNetworkCount.textContent = Number(data.total_networks || 0);
        elements.wifiAccessPointCount.textContent = Number(data.total_access_points || 0);
        elements.wifiScanStatus.textContent =
            `Last scan: ${formatTimestamp(data.scanned_at)}`;

        const rows = [];

        networks.forEach(network => {
            const points = network.access_points || [];

            if (!points.length) {
                rows.push(`
                    <tr>
                        <td>${escapeHTML(network.ssid)}</td>
                        <td>Unknown</td><td>Unknown</td><td>--</td>
                        <td>${escapeHTML(network.authentication)}</td>
                        <td>Unknown</td><td>--</td>
                    </tr>
                `);
                return;
            }

            points.forEach(point => {
                const signal = Number(point.signal);
                const valid = Number.isFinite(signal) && signal >= 0 && signal <= 100;

                rows.push(`
                    <tr>
                        <td class="wifi-ssid">${escapeHTML(network.ssid)}</td>
                        <td>
                            <div class="signal-cell">
                                <span>${valid ? signal + "%" : "Unknown"}</span>
                                <div class="signal-track">
                                    <div class="signal-fill" style="width:${valid ? signal : 0}%"></div>
                                </div>
                            </div>
                        </td>
                        <td>${escapeHTML(point.band || "Unknown")}</td>
                        <td>${point.channel ?? "--"}</td>
                        <td>${escapeHTML(network.authentication || "Unknown")}</td>
                        <td>${escapeHTML(point.radio_type || "Unknown")}</td>
                        <td class="bssid-cell">${escapeHTML(point.bssid || "--")}</td>
                    </tr>
                `);
            });
        });

        elements.wifiNetworkTable.innerHTML = rows.length
            ? rows.join("")
            : `<tr><td colspan="7" class="empty-state">No nearby Wi-Fi networks detected.</td></tr>`;

    } catch (error) {
        elements.wifiScanStatus.textContent = "Scan failed. Try again.";
        elements.wifiNetworkTable.innerHTML =
            `<tr><td colspan="7" class="empty-state">Unable to retrieve nearby Wi-Fi networks.</td></tr>`;
        console.error("Wi-Fi scan failed:", error);
    }
}

async function refreshDashboard() {
    await Promise.all([
        updateNetworkStats(),
        updateNetworkStatus(),
        updateTrafficHistory()
    ]);
}

document.addEventListener("DOMContentLoaded", () => {
    initializeChart();
    refreshDashboard();
    updateWifiNetworks();

    elements.scanWifiButton.addEventListener("click", async () => {
        elements.scanWifiButton.disabled = true;
        elements.scanWifiButton.textContent = "Scanning...";
        await updateWifiNetworks();
        elements.scanWifiButton.disabled = false;
        elements.scanWifiButton.textContent = "Scan Again";
    });

    setInterval(refreshDashboard, REFRESH_INTERVAL);
    setInterval(updateWifiNetworks, 15000);
});
