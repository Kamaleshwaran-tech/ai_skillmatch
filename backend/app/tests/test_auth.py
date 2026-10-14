"""Unit tests for authentication and user management."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# In-memory SQLite database specifically for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_register_user_success(client):
    """Test user registration endpoint with valid payload."""
    payload = {
        "email": "testuser@example.com",
        "password": "Password123!",
        "full_name": "Test User",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "testuser@example.com"
    assert data["user"]["full_name"] == "Test User"
    assert data["user"]["is_active"] is True


def test_register_duplicate_email_fails(client):
    """Test that registering an existing email returns 400 Bad Request."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Original User",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_login_success_and_get_me(client):
    """Test login with credentials and accessing /me endpoint."""
    # Register first
    reg_payload = {
        "email": "authme@example.com",
        "password": "SecurePassword99",
        "full_name": "Auth Me",
    }
    client.post("/api/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "authme@example.com",
        "password": "SecurePassword99",
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Access /api/auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "authme@example.com"
    assert me_data["full_name"] == "Auth Me"


def test_login_invalid_password_fails(client):
    """Test login with invalid password returns 401 Unauthorized."""
    reg_payload = {
        "email": "wrongpwd@example.com",
        "password": "CorrectPassword1",
    }
    client.post("/api/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/auth/login",
        json={"email": "wrongpwd@example.com", "password": "WrongPassword2"},
    )
    assert login_res.status_code == 401
    assert "Incorrect email or password" in login_res.json()["detail"]


def test_get_me_unauthorized_without_token(client):
    """Test /api/auth/me returns 401 when no token is provided."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
