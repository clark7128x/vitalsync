from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.consent import ConsentWithdraw
from app.services import privacy_service

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.post("/consent/withdraw")
async def withdraw_consent(
    payload: ConsentWithdraw,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await privacy_service.withdraw_consent(db, user.id, payload.consent_type)
    return {"status": "withdrawn", "consent_type": record.consent_type.value}


@router.get("/export")
async def export_my_data(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await privacy_service.export_user_data(db, user)


@router.post("/delete-request")
async def request_deletion(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await privacy_service.request_deletion(db, user)
    return {"status": "deletion_processed"}
