from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut, SubscriptionUpgrade
from app.services import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionOut, status_code=201)
async def create_subscription(
    payload: SubscriptionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await subscription_service.get_active_subscription(db, user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Active subscription already exists")
    return await subscription_service.create_subscription(db, user.id, payload.plan)


@router.get("/me", response_model=SubscriptionOut)
async def my_subscription(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = await subscription_service.get_active_subscription(db, user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")
    return sub


@router.post("/me/upgrade", response_model=SubscriptionOut)
async def upgrade(
    payload: SubscriptionUpgrade,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await subscription_service.get_active_subscription(db, user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")
    return await subscription_service.upgrade_subscription(db, sub, payload.plan)


@router.post("/me/cancel", response_model=SubscriptionOut)
async def cancel(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = await subscription_service.get_active_subscription(db, user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")
    return await subscription_service.cancel_subscription(db, sub)
