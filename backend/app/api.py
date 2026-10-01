from fastapi import APIRouter

from app.routes.auth.router import router as auth_router
from app.routes.charts.router import router as charts_router
from app.routes.jobs.router import router as jobs_router
from app.routes.matches.router import router as matches_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(charts_router)
api_router.include_router(jobs_router)
api_router.include_router(matches_router)