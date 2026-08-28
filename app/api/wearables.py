from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import enforce_rate_limit
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.wearable import WearableReading
from app.schemas.wearable import WearableReadingIn, WearableReadingOut

router = APIRouter(prefix="/wearables", tags=["wearables"])


@router.post("/readings", response_model=list[WearableReadingOut], status_code=201)
async def ingest_readings(
    payload: list[WearableReadingIn],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Wearable syncs can fire bursts of requests (a watch flushing its
    # buffer after being offline); protect the DB without punishing normal
    # usage by limiting per-user rather than globally.
    await enforce_rate_limit(f"wearable-ingest:{user.id}")

    rows = [
        WearableReading(
            user_id=user.id,
            source=r.source,
            metric_type=r.metric_type,
            value=r.value,
            unit=r.unit,
            recorded_at=r.recorded_at,
        )
        for r in payload
    ]
    db.add_all(rows)
    await db.commit()
    for row in rows:
        await db.refresh(row)
    return rows
