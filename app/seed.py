from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .models import AIEvent, EventType, Worker, Workstation


def generate_sample_workers() -> list[Worker]:
    return [Worker(worker_id=f"W{i}", name=f"Worker {i}") for i in range(1, 7)]


def generate_sample_workstations() -> list[Workstation]:
    station_types = ["Assembly", "Packaging", "Inspection", "Welding", "Painting", "Dispatch"]
    return [Workstation(station_id=f"S{i}", name=station_types[i - 1]) for i in range(1, 7)]


def generate_sample_events() -> list[AIEvent]:
    events: list[AIEvent] = []
    base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(hours=8)

    for i in range(1, 7):
        wid = f"W{i}"
        sid = f"S{i}"
        # Repeated hourly blocks with working/idle and product counts
        for hour in range(8):
            t = base + timedelta(hours=hour)
            if hour % 4 == 3:
                events.append(
                    AIEvent(
                        timestamp=t,
                        worker_id=wid,
                        workstation_id=sid,
                        event_type=EventType.idle,
                        confidence=0.90,
                        count=1,
                    )
                )
            else:
                events.append(
                    AIEvent(
                        timestamp=t,
                        worker_id=wid,
                        workstation_id=sid,
                        event_type=EventType.working,
                        confidence=0.95,
                        count=1,
                    )
                )
                events.append(
                    AIEvent(
                        timestamp=t + timedelta(minutes=30),
                        worker_id=wid,
                        workstation_id=sid,
                        event_type=EventType.product_count,
                        confidence=0.97,
                        count=5 + i,
                    )
                )
    return sorted(events, key=lambda e: e.timestamp)


def reset_and_seed(db: Session) -> dict:
    db.query(AIEvent).delete()
    db.query(Worker).delete()
    db.query(Workstation).delete()
    db.commit()

    workers = generate_sample_workers()
    stations = generate_sample_workstations()
    events = generate_sample_events()

    db.add_all(workers)
    db.add_all(stations)
    db.add_all(events)
    db.commit()

    return {"status": "seeded", "workers": len(workers), "workstations": len(stations), "events": len(events)}
