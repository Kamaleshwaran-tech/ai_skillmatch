"""SkillSync AI - FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import api_router
from app.db.session import engine
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    # Ensure database connection can be established
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        print(f"Database connection warning on startup: {exc}")

    # Load and warm up the semantic matcher model once at process startup
    try:
        from app.services.semantic_matcher import semantic_matcher
        _ = semantic_matcher.encode("warmup")
        print("Semantic Matcher model successfully loaded and warmed up at process startup.")
    except Exception as exc:
        print(f"Warning: Semantic matcher warmup encountered issue: {exc}")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Skill Gap Analyzer & Market-Driven Career Pathway Generator",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend operational readiness."""
    db_status = "healthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unreachable: {str(e)}"

    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": db_status,
            "dialect": engine.dialect.name,
        },
    }


# Include all modular API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint welcoming API consumers."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": "/api/health",
    }
