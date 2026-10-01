from app.models.jobs import Job
from app.routes.jobs.router import enqueue_job

# For specific jobs that need to be enqueued without an endpoint
def enqueue_tachi_seed(db, user_id: int) -> Job:
    return enqueue_job(db, user_id, "tachi_seed_profile", {"playtype": "7k"})