import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConsentType(str, enum.Enum):
    data_processing = "data_processing"
    marketing = "marketing"
    wearable_sharing = "wearable_sharing"


class ConsentRecord(Base):
    """
    Append-only log rather than a single mutable row per user: keeps a full
    audit trail of what was granted or withdrawn, and when. Regulators tend
    to ask "prove consent was in place on date X", not just "is it on now".
    """

    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    consent_type: Mapped[ConsentType] = mapped_column(Enum(ConsentType), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=True)

    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
