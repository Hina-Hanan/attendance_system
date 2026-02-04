from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# Load .env from backend folder first (so it's always found regardless of cwd)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"
if _ENV_FILE.exists():
    load_dotenv(dotenv_path=_ENV_FILE, override=True)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/attendance_db"
    
    # Face Recognition
    FACE_ENCODING_DIMENSION: int = 128
    FACE_MATCH_THRESHOLD: float = 0.6  # Lower = stricter; used for display/fallback
    FACE_AUTH_THRESHOLD: float = 0.5  # Stricter for login (reduce wrong-person match)
    FACE_AUTH_AMBIGUITY_MARGIN: float = 0.08  # Reject if best and second-best match are too close
    FACE_DUPLICATE_CHECK_THRESHOLD: float = 0.42  # Only block when very close match (allows siblings to register)
    FACE_ENCODING_NUM_JITTERS: int = 3  # Higher = more stable encoding (slower)
    MIN_FACE_IMAGES_REQUIRED: int = 3
    MAX_FACE_IMAGES_REQUIRED: int = 4
    
    # Spoof Prevention
    SPOOF_CHECK_FRAMES: int = 5  # Number of frames to check for movement
    BLINK_DETECTION_THRESHOLD: float = 0.25  # EAR threshold for blink detection
    HEAD_MOVEMENT_THRESHOLD: float = 0.1  # Minimum head movement required
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    
    model_config = {
        **({"env_file": str(_ENV_FILE)} if _ENV_FILE.exists() else {}),
        "case_sensitive": True,
    }


settings = Settings()
