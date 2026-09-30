from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.charts.router import router as charts_router
from app.jobs.router import router as jobs_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(charts_router)
api_router.include_router(jobs_router)