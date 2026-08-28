from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.events.outbox import record_event
from app.models.consent import ConsentRecord, ConsentType
from app.models.user import User


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str | None,
    referred_by_code: str | None,
) -> User:
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        referred_by_code=referred_by_code,
    )
    db.add(user)
    await db.flush()  # assigns user.id without ending the transaction

    # Using the product at all requires this consent, so we record it as
    # granted at signup rather than treating "no record" as implicit consent.
    db.add(ConsentRecord(user_id=user.id, consent_type=ConsentType.data_processing, granted=True))

    await record_event(
        db,
        "user.registered",
        {"user_id": user.id, "email": user.email, "referred_by_code": referred_by_code},
    )

    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower(), User.is_deleted.is_(False)))
    return result.scalar_one_or_none()
