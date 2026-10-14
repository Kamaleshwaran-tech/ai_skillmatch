from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment configuration."""

    PROJECT_NAME: str = "SkillSync AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api"

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    # Database Configuration (defaults to SQLite, ready for PostgreSQL)
    DATABASE_URL: str = "sqlite:///./skillsync.db"

    # Authentication & Security
    JWT_SECRET: str = "changethis_supersecretkey_for_jwt_auth_min_32_chars_long_12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # External APIs - Job Market Demand (Adzuna)
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    ADZUNA_COUNTRY: str = "us"

    # AI / Semantic Matching Engine
    SEMANTIC_MODEL_NAME: str = "all-MiniLM-L6-v2"
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.65

    # LLM Configuration for Learning Roadmap Explanations
    LLM_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL_NAME: str = "gemini-2.0-flash"
    LLM_API_URL: str = ""
    LLM_TIMEOUT_SECONDS: float = 8.0

    # File storage
    UPLOAD_DIR: str = "./uploads/resumes"
    MAX_UPLOAD_SIZE_MB: int = 5

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
