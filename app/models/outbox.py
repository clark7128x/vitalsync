import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OutboxEvent(Base):
    """
    Transactional outbox. Written in the SAME database transaction as the
    business change it describes (see app/events/outbox.py), so a commit can
    never succeed while silently failing to record the event, or vice versa.
    A separate relay process (app/events/publisher.py) delivers rows here to
    RabbitMQ and marks them published — the API process never talks to the
    broker directly.
    """

    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
