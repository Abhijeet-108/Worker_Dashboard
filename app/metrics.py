from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .models import AIEvent


@dataclass
class DurationStats:
    working_minutes: float = 0.0
    idle_minutes: float = 0.0
    absent_minutes: float = 0.0
    units_produced: int = 0

    @property
    def active_minutes(self) -> float:
        return self.working_minutes

    @property
    def total_timed_minutes(self) -> float:
        return self.working_minutes + self.idle_minutes + self.absent_minutes

    @property
    def utilization_pct(self) -> float:
        if self.total_timed_minutes <= 0:
            return 0.0
        return (self.working_minutes / self.total_timed_minutes) * 100

    @property
    def units_per_hour(self) -> float:
        if self.working_minutes <= 0:
            return 0.0
        return self.units_produced / (self.working_minutes / 60)


def _minutes_between(ts1: datetime, ts2: datetime) -> float:
    return max((ts2 - ts1).total_seconds() / 60.0, 0.0)


def compute_metrics(events: Iterable[AIEvent], workers: list[dict], workstations: list[dict]) -> dict:
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    worker_stats: dict[str, DurationStats] = {w["worker_id"]: DurationStats() for w in workers}
    station_stats: dict[str, DurationStats] = {s["station_id"]: DurationStats() for s in workstations}

    worker_timeline: dict[str, list[AIEvent]] = defaultdict(list)
    station_timeline: dict[str, list[AIEvent]] = defaultdict(list)

    for event in sorted_events:
        worker_timeline[event.worker_id].append(event)
        station_timeline[event.workstation_id].append(event)
        if event.event_type.value == "product_count":
            worker_stats[event.worker_id].units_produced += event.count
            station_stats[event.workstation_id].units_produced += event.count

    # Duration attribution assumption:
    # each status event (working/idle/absent) represents state until next status event for that entity.
    for worker_id, timeline in worker_timeline.items():
        for curr, nxt in zip(timeline, timeline[1:]):
            if curr.event_type.value not in {"working", "idle", "absent"}:
                continue
            minutes = _minutes_between(curr.timestamp, nxt.timestamp)
            if curr.event_type.value == "working":
                worker_stats[worker_id].working_minutes += minutes
            elif curr.event_type.value == "idle":
                worker_stats[worker_id].idle_minutes += minutes
            elif curr.event_type.value == "absent":
                worker_stats[worker_id].absent_minutes += minutes

    for station_id, timeline in station_timeline.items():
        for curr, nxt in zip(timeline, timeline[1:]):
            if curr.event_type.value not in {"working", "idle", "absent"}:
                continue
            minutes = _minutes_between(curr.timestamp, nxt.timestamp)
            if curr.event_type.value == "working":
                station_stats[station_id].working_minutes += minutes
            elif curr.event_type.value == "idle":
                station_stats[station_id].idle_minutes += minutes
            elif curr.event_type.value == "absent":
                station_stats[station_id].absent_minutes += minutes

    worker_metrics = []
    for worker in workers:
        ws = worker_stats[worker["worker_id"]]
        worker_metrics.append(
            {
                "worker_id": worker["worker_id"],
                "name": worker["name"],
                "active_time_minutes": round(ws.active_minutes, 2),
                "idle_time_minutes": round(ws.idle_minutes, 2),
                "utilization_pct": round(ws.utilization_pct, 2),
                "units_produced": ws.units_produced,
                "units_per_hour": round(ws.units_per_hour, 2),
            }
        )

    station_metrics = []
    for station in workstations:
        ss = station_stats[station["station_id"]]
        station_metrics.append(
            {
                "station_id": station["station_id"],
                "name": station["name"],
                "occupancy_time_minutes": round(ss.active_minutes + ss.idle_minutes, 2),
                "utilization_pct": round(ss.utilization_pct, 2),
                "units_produced": ss.units_produced,
                "throughput_rate_per_hour": round(ss.units_per_hour, 2),
            }
        )

    total_productive_minutes = sum(w["active_time_minutes"] for w in worker_metrics)
    total_production_count = sum(w["units_produced"] for w in worker_metrics)
    avg_production_rate = (
        sum(w["units_per_hour"] for w in worker_metrics) / len(worker_metrics) if worker_metrics else 0.0
    )
    avg_worker_utilization = (
        sum(w["utilization_pct"] for w in worker_metrics) / len(worker_metrics) if worker_metrics else 0.0
    )

    return {
        "factory": {
            "total_productive_time_minutes": round(total_productive_minutes, 2),
            "total_production_count": total_production_count,
            "average_production_rate_per_hour": round(avg_production_rate, 2),
            "average_worker_utilization_pct": round(avg_worker_utilization, 2),
        },
        "workers": worker_metrics,
        "workstations": station_metrics,
    }
