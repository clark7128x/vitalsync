from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.outbox import record_event
from app.models.consent import ConsentRecord, ConsentType
from app.models.subscription import Subscription
from app.models.user import User
from app.models.wearable import WearableReading


async def withdraw_consent(db: AsyncSession, user_id: str, consent_type: ConsentType) -> ConsentRecord:
    record = ConsentRecord(
        user_id=user_id,
        consent_type=consent_type,
        granted=False,
        revoked_at=datetime.now(timezone.utc),
    )
    db.add(record)

    await record_event(db, "consent.withdrawn", {"user_id": user_id, "consent_type": consent_type.value})

    await db.commit()
    await db.refresh(record)
    return record


async def export_user_data(db: AsyncSession, user: User) -> dict:
    """Full self-service export: every table that stores something about
    this user, in one JSON document. This is the whole point of a "right to
    portability" endpoint — no support ticket, no manual DB query."""
    subs = (await db.execute(select(Subscription).where(Subscription.user_id == user.id))).scalars().all()
    readings = (await db.execute(select(WearableReading).where(WearableReading.user_id == user.id))).scalars().all()
    consents = (await db.execute(select(ConsentRecord).where(ConsentRecord.user_id == user.id))).scalars().all()

    return {
        "profile": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat(),
        },
        "subscriptions": [{"plan": s.plan.value, "status": s.status.value} for s in subs],
        "wearable_readings": [
            {
                "metric_type": r.metric_type,
                "value": r.value,
                "unit": r.unit,
                "recorded_at": r.recorded_at.isoformat(),
            }
            for r in readings
        ],
        "consents": [{"type": c.consent_type.value, "granted": c.granted} for c in consents],
    }


async def request_deletion(db: AsyncSession, user: User) -> None:
    """
    Anonymize rather than hard-delete. Billing/subscription history often
    has to survive for accounting or legal reasons even after an erasure
    request; what has to go is anything that identifies the person. This
    keeps foreign keys intact while scrubbing PII from the user row itself.
    """
    user.email = f"deleted-{user.id}@removed.local"
    user.full_name = None
    user.hashed_password = "removed"  # noqa: S105 - not a real credential
    user.is_active = False
    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)

    await record_event(db, "user.deletion_requested", {"user_id": user.id})

    await db.commit()
