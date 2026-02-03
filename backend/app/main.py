from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import engine, Base
from app.routes import api_router

# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure user_number column exists (for DBs created before it was added)
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS user_number INTEGER UNIQUE"))
except Exception:
    pass  # Column may already exist or table not created yet

# Create FastAPI app
app = FastAPI(
    title="Face Authentication Attendance System",
    description="A production-ready face authentication based attendance system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "message": "Face Authentication Attendance System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
