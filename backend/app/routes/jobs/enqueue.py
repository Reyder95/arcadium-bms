from datetime import datetime, timedelta

from app.models.jobs import Job
from app.routes.jobs.router import enqueue_job

# For specific jobs that need to be enqueued without an endpoint
def enqueue_tachi_seed(db, user_id: int) -> Job:
    return enqueue_job(db, user_id, "tachi_seed_profile", {"playtype": "7k"})

def enqueue_match_final_check(db, user_id: int, match_id: int, match_cutoff: datetime) -> Job:
    return enqueue_job(db, user_id, "match_end_check", {"matchId": match_id}, run_after=match_cutoff)

def enqueue_match_pre_submission(db, user_id: int, match_id: int) -> Job:
    return enqueue_job(db, user_id, "match_pre_submission", {"matchId": match_id})