import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import AuthSession, User


password_hasher = PasswordHasher()


class AuthService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def hash_password(self, password: str) -> str:
        return password_hasher.hash(password)

    def verify_password(self, password_hash: str, password: str) -> bool:
        try:
            return password_hasher.verify(password_hash, password)
        except VerifyMismatchError:
            return False

    def hash_token(self, token: str) -> str:
        material = f"{self.settings.session_token_pepper}:{token}".encode()
        return hashlib.sha256(material).hexdigest()

    async def login(self, db: AsyncSession, email: str, password: str) -> tuple[User, str, datetime] | None:
        result = await db.execute(select(User).where(User.email == email.lower().strip()))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active or not self.verify_password(user.password_hash, password):
            return None

        token = secrets.token_urlsafe(48)
        expires_at = datetime.now(UTC) + timedelta(minutes=self.settings.session_ttl_minutes)
        db.add(
            AuthSession(
                user_id=user.id,
                token_hash=self.hash_token(token),
                expires_at=expires_at,
            )
        )
        await db.commit()
        return user, token, expires_at

    async def logout(self, db: AsyncSession, token: str) -> None:
        await db.execute(
            update(AuthSession)
            .where(AuthSession.token_hash == self.hash_token(token), AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await db.commit()

