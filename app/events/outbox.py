from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent


async def record_event(db: AsyncSession, event_type: str, payload: dict) -> None:
    """
    Stage an event inside the caller's current transaction.

    Deliberately does NOT commit. The caller must commit once, so the
    business row(s) and this outbox row land together or not at all. Never
    call this in its own transaction, and never publish to RabbitMQ directly
    from a request handler — that's how you get an event for a change that
    later rolled back, or a committed change nobody ever heard about.
    """
    db.add(OutboxEvent(event_type=event_type, payload=payload))
