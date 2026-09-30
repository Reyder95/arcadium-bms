from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.charts.router import router as charts_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(charts_router)