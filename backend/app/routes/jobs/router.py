from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime

from app.dependencies import CurrentUser
from app.models import Job
from app.db import DbSession

ACTIVE_STATUSES = ("pending", "running")

def enqueue_job(db: Session, user_id: int, job_type: str, payload: dict | None = None, run_after: datetime | None = None):
    payload = payload or {}

    existing = db.scalar(
        select(Job).where(
            Job.user_id == user_id,
            Job.type == job_type,
            Job.payload == payload,
            Job.status.in_(ACTIVE_STATUSES)
        )
    )

    if existing:
        return existing

    job = Job(user_id=user_id, type=job_type, payload=payload, run_after=run_after if not None else func.now())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    type: str
    status: str
    result: dict | None
    error: str | None

def check_tachi_key(user: CurrentUser):
    if not user.tachi_api_key:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link your Bokutachi account first!")

@router.post("/tachi-recent-score", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def request_tachi_recent_score(user: CurrentUser, db: DbSession):
    check_tachi_key(user)

    return enqueue_job(db, user.id, "tachi_recent_score", {"playtype": "7k"})

@router.post("/tachi-rating", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def request_tachi_rating(user: CurrentUser, db: DbSession):
    check_tachi_key(user)

    return enqueue_job(db, user.id, "tachi_rating", {"playtype": "7k"})

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, user: CurrentUser, db: DbSession):
    job = db.get(Job, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")

    return job

@router.post("/{job_id}/retry", response_model=JobOut)
def retry_job(job_id: int, user: CurrentUser, db: DbSession):
    job = db.get(Job, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    job.status = "pending"
    job.run_after = func.now()
    job.error = None

    db.commit()
    db.refresh(job)

    return job