let fullData = null;

const factoryCards = document.getElementById("factoryCards");
const workersBody = document.getElementById("workersBody");
const stationsBody = document.getElementById("stationsBody");
const workerFilter = document.getElementById("workerFilter");
const stationFilter = document.getElementById("stationFilter");

document.getElementById("refreshBtn").addEventListener("click", loadMetrics);
document.getElementById("seedBtn").addEventListener("click", async () => {
  await fetch("/api/seed/reset", { method: "POST" });
  await loadMetrics();
});
workerFilter.addEventListener("change", render);
stationFilter.addEventListener("change", render);

function mkCard(label, value) {
  return `<div class="card"><strong>${label}</strong><div>${value}</div></div>`;
}

function render() {
  if (!fullData) return;
  const wf = workerFilter.value;
  const sf = stationFilter.value;

  const workers = wf === "all" ? fullData.workers : fullData.workers.filter((w) => w.worker_id === wf);
  const stations = sf === "all" ? fullData.workstations : fullData.workstations.filter((s) => s.station_id === sf);

  const factory = fullData.factory;
  factoryCards.innerHTML = [
    mkCard("Total Productive Time (min)", factory.total_productive_time_minutes),
    mkCard("Total Production Count", factory.total_production_count),
    mkCard("Avg Production Rate (/hr)", factory.average_production_rate_per_hour),
    mkCard("Avg Worker Utilization %", factory.average_worker_utilization_pct),
  ].join("");

  workersBody.innerHTML = workers
    .map(
      (w) => `<tr><td>${w.worker_id}</td><td>${w.name}</td><td>${w.active_time_minutes}</td><td>${w.idle_time_minutes}</td><td>${w.utilization_pct}</td><td>${w.units_produced}</td><td>${w.units_per_hour}</td></tr>`
    )
    .join("");

  stationsBody.innerHTML = stations
    .map(
      (s) => `<tr><td>${s.station_id}</td><td>${s.name}</td><td>${s.occupancy_time_minutes}</td><td>${s.utilization_pct}</td><td>${s.units_produced}</td><td>${s.throughput_rate_per_hour}</td></tr>`
    )
    .join("");
}

async function loadMetrics() {
  const res = await fetch("/api/metrics");
  fullData = await res.json();

  const workerIds = fullData.workers.map((w) => w.worker_id);
  const stationIds = fullData.workstations.map((s) => s.station_id);

  workerFilter.innerHTML = '<option value="all">All</option>' + workerIds.map((id) => `<option value="${id}">${id}</option>`).join("");
  stationFilter.innerHTML = '<option value="all">All</option>' + stationIds.map((id) => `<option value="${id}">${id}</option>`).join("");

  render();
}

loadMetrics();
