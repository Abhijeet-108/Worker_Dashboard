import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class EventType(str, enum.Enum):
    working = "working"
    idle = "idle"
    absent = "absent"
    product_count = "product_count"


class Worker(Base):
    __tablename__ = "workers"

    worker_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    events = relationship("AIEvent", back_populates="worker")


class Workstation(Base):
    __tablename__ = "workstations"

    station_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    events = relationship("AIEvent", back_populates="workstation")


class AIEvent(Base):
    __tablename__ = "ai_events"
    __table_args__ = (
        UniqueConstraint(
            "timestamp", "worker_id", "workstation_id", "event_type", "count", name="uq_event_dedup"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    worker_id = Column(String, ForeignKey("workers.worker_id"), nullable=False, index=True)
    workstation_id = Column(String, ForeignKey("workstations.station_id"), nullable=False, index=True)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    count = Column(Integer, nullable=False, default=1)

    worker = relationship("Worker", back_populates="events")
    workstation = relationship("Workstation", back_populates="events")
