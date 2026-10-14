"""Authentication service handling registration, credential verification, and token issuance."""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate, UserLogin, Token, UserOut
from app.core.security import verify_password, create_access_token
from app.models import User


class AuthService:
    """Service encapsulating user registration and authentication logic."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, user_in: UserCreate) -> Token:
        """Register a new user and issue an access token."""
        existing_user = self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        new_user = self.user_repo.create(user_in)
        token = create_access_token(subject=str(new_user.id))
        return Token(
            access_token=token,
            token_type="bearer",
            user=UserOut.model_validate(new_user),
        )

    def authenticate(self, credentials: UserLogin) -> Token:
        """Verify user credentials and return an access token."""
        user = self.user_repo.get_by_email(credentials.email)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account.",
            )

        token = create_access_token(subject=str(user.id))
        return Token(
            access_token=token,
            token_type="bearer",
            user=UserOut.model_validate(user),
        )
