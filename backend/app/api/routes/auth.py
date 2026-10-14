"""Authentication routes (Registration, Login, Current User Me)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models import User
from app.schemas.auth import UserCreate, UserLogin, UserOut, Token
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a new user account and receive an initial JWT access token."""
    auth_service = AuthService(db)
    return auth_service.register(user_in)


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User login with email and password",
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate user with email and password and receive a JWT access token."""
    auth_service = AuthService(db)
    return auth_service.authenticate(credentials)


@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of the currently authenticated user using Bearer token."""
    return current_user
