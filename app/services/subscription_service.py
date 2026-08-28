from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.outbox import record_event
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus

PLAN_DURATIONS = {
    SubscriptionPlan.monthly: timedelta(days=30),
    SubscriptionPlan.quarterly: timedelta(days=90),
    SubscriptionPlan.annual: timedelta(days=365),
}


async def get_active_subscription(db: AsyncSession, user_id: str) -> Subscription | None:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status != SubscriptionStatus.canceled)
        .order_by(Subscription.created_at.desc())
    )
    return result.scalars().first()


async def create_subscription(db: AsyncSession, user_id: str, plan: SubscriptionPlan) -> Subscription:
    now = datetime.now(timezone.utc)
    sub = Subscription(
        user_id=user_id,
        plan=plan,
        status=SubscriptionStatus.trialing,
        current_period_start=now,
        current_period_end=now + PLAN_DURATIONS[plan],
    )
    db.add(sub)
    await db.flush()

    await record_event(
        db,
        "subscription.created",
        {"subscription_id": sub.id, "user_id": user_id, "plan": plan.value, "status": sub.status.value},
    )

    await db.commit()
    await db.refresh(sub)
    return sub


async def upgrade_subscription(db: AsyncSession, subscription: Subscription, new_plan: SubscriptionPlan) -> Subscription:
    old_plan = subscription.plan
    subscription.plan = new_plan
    subscription.status = SubscriptionStatus.active
    subscription.current_period_end = datetime.now(timezone.utc) + PLAN_DURATIONS[new_plan]

    await record_event(
        db,
        "subscription.upgraded",
        {
            "subscription_id": subscription.id,
            "user_id": subscription.user_id,
            "old_plan": old_plan.value,
            "new_plan": new_plan.value,
        },
    )

    await db.commit()
    await db.refresh(subscription)
    return subscription


async def cancel_subscription(db: AsyncSession, subscription: Subscription) -> Subscription:
    subscription.status = SubscriptionStatus.canceled
    subscription.canceled_at = datetime.now(timezone.utc)

    await record_event(
        db,
        "subscription.canceled",
        {"subscription_id": subscription.id, "user_id": subscription.user_id},
    )

    await db.commit()
    await db.refresh(subscription)
    return subscription
