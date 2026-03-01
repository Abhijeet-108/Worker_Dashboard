# AI-Powered Worker Productivity Dashboard

A full-stack technical assessment app that ingests AI CCTV events, stores them in SQLite, computes productivity KPIs, and renders a dashboard for 6 workers and 6 workstations.

## Live App Link
Run locally and open: `http://localhost:8000`

## Architecture (Edge → Backend → Dashboard)

1. **Edge / Camera AI system** emits structured JSON events.
2. **Backend API (FastAPI)** accepts batch event ingestion at `POST /api/events`.
3. **SQLite database** persists workers, workstations, and all AI events.
4. **Metrics service** computes worker/station/factory metrics from stored events.
5. **Dashboard UI** (vanilla JS + HTML/CSS) fetches `GET /api/metrics` and renders summary + tables.

## Features Implemented

- Seeded sample setup for **6 workers** + **6 workstations**.
- Persistent event storage with duplicate detection.
- APIs:
  - `POST /api/events` (ingest event batches)
  - `GET /api/metrics` (computed productivity KPIs)
  - `POST /api/seed/reset` (reinitialize dummy data)
- Worker-level, workstation-level, and factory-level metrics.
- Filter controls in the dashboard for worker and workstation.
- Dockerized deployment.

## Database Schema

### workers
- `worker_id` (PK)
- `name`

### workstations
- `station_id` (PK)
- `name`

### ai_events
- `id` (PK)
- `timestamp`
- `worker_id` (FK → workers)
- `workstation_id` (FK → workstations)
- `event_type` (`working | idle | absent | product_count`)
- `confidence`
- `count`
- Unique constraint for deduplication:
  - `(timestamp, worker_id, workstation_id, event_type, count)`

## Metrics Definitions

### Worker-level
- **Total active time**: sum of minutes where event state is `working`.
- **Total idle time**: sum of minutes where event state is `idle`.
- **Utilization %**: `working / (working + idle + absent) * 100`.
- **Total units produced**: sum of `count` from `product_count` events.
- **Units/hour**: `units_produced / (working_minutes / 60)`.

### Workstation-level
- **Occupancy time**: `working + idle` minutes.
- **Utilization %**: `working / (working + idle + absent) * 100`.
- **Total units produced**: sum of `count` from `product_count` events at station.
- **Throughput rate**: same calculation basis as units/hour (using station working time).

### Factory-level
- **Total productive time**: sum of all worker active minutes.
- **Total production count**: sum of all worker units produced.
- **Average production rate**: average worker units/hour.
- **Average utilization**: average worker utilization %.

## Time Assumptions / Aggregation Logic

- Status events (`working`, `idle`, `absent`) are treated as a state that remains true until the **next event for that same entity**.
- Duration between consecutive timestamps is attributed to the earlier status event.
- `product_count` events contribute **only production count**, not duration.
- Out-of-order timestamps are handled by sorting events by timestamp before metric computation.

## Reliability Handling

### Intermittent connectivity
- Events are persisted on arrival and metrics are computed from stored history.
- In production, edge gateways should buffer unsent events and replay later.

### Duplicate events
- The unique database constraint prevents duplicate inserts.
- API returns inserted vs duplicate counts.

### Out-of-order timestamps
- Metrics pipeline sorts by timestamp each request, so late-arriving older events are included correctly.

## Model Lifecycle (theoretical)

### Add model versioning
- Add `model_version` field to `ai_events` and enforce version registry in DB.
- Compare KPI quality slices by model version.

### Detect model drift
- Track confidence distributions, event-type frequency shifts, and disagreement with sampled human audits.
- Trigger alerts when distributions diverge from training/reference baseline.

### Trigger retraining
- Schedule retraining when drift thresholds are crossed, KPI quality degrades, or concept drift is detected by site/shift.
- Roll out via staged canary deployment and compare operational KPIs before full release.

## Scaling Plan

### 5 cameras
- Current single-service + SQLite is adequate.

### 100+ cameras
- Move to managed DB (PostgreSQL), async ingestion queue (Kafka/RabbitMQ), and background metric materialization.

### Multi-site
- Site-partitioned event streams, multi-tenant schema, regional ingestion APIs, warehouse-level analytics, and centralized observability.

## Run Locally

### Option 1: Python
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000`

### Option 2: Docker
```bash
docker compose up --build
```

## API Examples

### Ingest events
```bash
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '[
    {
      "timestamp": "2026-01-15T10:15:00Z",
      "worker_id": "W1",
      "workstation_id": "S3",
      "event_type": "working",
      "confidence": 0.93,
      "count": 1
    },
    {
      "timestamp": "2026-01-15T10:20:00Z",
      "worker_id": "W1",
      "workstation_id": "S3",
      "event_type": "product_count",
      "confidence": 0.96,
      "count": 3
    }
  ]'
```

### Get metrics
```bash
curl http://localhost:8000/api/metrics
```

### Reset dummy data
```bash
curl -X POST http://localhost:8000/api/seed/reset
```
