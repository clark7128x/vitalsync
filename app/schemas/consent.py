from pydantic import BaseModel

from app.models.consent import ConsentType


class ConsentWithdraw(BaseModel):
    consent_type: ConsentType
