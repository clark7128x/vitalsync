from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WearableReadingIn(BaseModel):
    source: str
    metric_type: str
    value: float
    unit: str
    recorded_at: datetime


class WearableReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    metric_type: str
    value: float
    unit: str
    recorded_at: datetime
