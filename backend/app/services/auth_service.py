"""Authentication service for user management and JWT tokens."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt as bcrypt_lib
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User

# bcrypt work factor 12 (takes ~200-400ms to hash)
BCRYPT_WORK_FACTOR = 12


class AuthService:
    """Handles user authentication and token management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    # --- Password Hashing ---

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with work factor 12."""
        salt = bcrypt_lib.gensalt(rounds=BCRYPT_WORK_FACTOR)
        hashed = bcrypt_lib.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash using timing-safe comparison."""
        try:
            return bcrypt_lib.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    # --- JWT Token Management ---

    def create_access_token(self, user_id: str) -> str:
        """Create JWT access token with user_id as subject."""
        expire = datetime.now(UTC) + timedelta(minutes=self.settings.jwt_expire_minutes)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(UTC),
        }
        return jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def verify_token(self, token: str) -> str | None:
        """Verify JWT token and return user_id if valid."""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            user_id: str | None = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None

    # --- Delete Token (for anonymous uploads) ---

    @staticmethod
    def generate_delete_token() -> str:
        """Generate a secure 32-byte URL-safe delete token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_delete_token(token: str) -> str:
        """Hash delete token using SHA-256 for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def verify_delete_token(token: str, token_hash: str) -> bool:
        """Verify delete token against stored hash (timing-safe)."""
        computed_hash = hashlib.sha256(token.encode()).hexdigest()
        return secrets.compare_digest(computed_hash, token_hash)

    # --- User Management ---

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, email: str, password: str) -> User:
        """Create a new user with hashed password."""
        password_hash = self.hash_password(password)
        user = User(email=email, password_hash=password_hash)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user by email and password. Returns None if invalid."""
        user = await self.get_user_by_email(email)
        if user is None:
            # Run hash anyway to prevent timing attacks (user enumeration)
            self.hash_password(password)
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user
