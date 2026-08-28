from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.subscription import SubscriptionPlan, SubscriptionStatus


class SubscriptionCreate(BaseModel):
    plan: SubscriptionPlan


class SubscriptionUpgrade(BaseModel):
    plan: SubscriptionPlan


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
