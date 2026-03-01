from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .metrics import compute_metrics
from .models import AIEvent, EventType, Worker, Workstation
from .schemas import AIEventIn, IngestResponse, SeedResponse
from .seed import reset_and_seed

app = FastAPI(title="AI Worker Productivity Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def ensure_seed_data() -> None:
    db = SessionLocal()
    try:
        worker_count = db.query(Worker).count()
        if worker_count == 0:
            reset_and_seed(db)
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def dashboard_page() -> str:
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/events", response_model=IngestResponse)
def ingest_events(events: list[AIEventIn], db: Session = Depends(get_db)) -> IngestResponse:
    inserted = 0
    duplicates = 0

    worker_ids = {w.worker_id for w in db.query(Worker).all()}
    station_ids = {s.station_id for s in db.query(Workstation).all()}

    for event in events:
        if event.worker_id not in worker_ids:
            raise HTTPException(status_code=400, detail=f"Unknown worker_id: {event.worker_id}")
        if event.workstation_id not in station_ids:
            raise HTTPException(status_code=400, detail=f"Unknown workstation_id: {event.workstation_id}")

        model = AIEvent(
            timestamp=event.timestamp,
            worker_id=event.worker_id,
            workstation_id=event.workstation_id,
            event_type=EventType(event.event_type),
            confidence=event.confidence,
            count=event.count,
        )
        db.add(model)
        try:
            db.commit()
            inserted += 1
        except IntegrityError:
            db.rollback()
            duplicates += 1

    return IngestResponse(inserted=inserted, duplicates=duplicates)


@app.get("/api/metrics")
def get_metrics(db: Session = Depends(get_db)) -> dict:
    workers = db.query(Worker).all()
    stations = db.query(Workstation).all()
    events = db.query(AIEvent).all()
    return compute_metrics(
        events,
        workers=[{"worker_id": w.worker_id, "name": w.name} for w in workers],
        workstations=[{"station_id": s.station_id, "name": s.name} for s in stations],
    )


@app.post("/api/seed/reset", response_model=SeedResponse)
def seed_reset(db: Session = Depends(get_db)) -> SeedResponse:
    return SeedResponse(**reset_and_seed(db))
