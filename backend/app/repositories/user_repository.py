"""User repository for database operations on the User model."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import User
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash


class UserRepository:
    """Repository handling User database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by primary key ID."""
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        stmt = select(User).where(User.email == email.lower().strip())
        return self.db.scalars(stmt).first()

    def create(self, user_in: UserCreate) -> User:
        """Create and persist a new user."""
        db_user = User(
            email=user_in.email.lower().strip(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=True,
            is_superuser=False,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
