from fastapi import APIRouter
from app.routes import auth, attendance, users, export

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
