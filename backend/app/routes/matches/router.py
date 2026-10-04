from fastapi import APIRouter, status, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.db import DbSession
from app.util.enums import CancelReason, MatchStatus
from app.models import Match, UserAvoidedChart
from app.util.dependencies import CurrentUser
from app.util.helpers import create_match_helper
from app.job.enqueue import enqueue_match_pre_submission

from app.schemas.match import MatchOut

router = APIRouter(prefix="/match", tags=["match"])

@router.get("/{match_id}", response_model=MatchOut, status_code=status.HTTP_200_OK)
def get_match_by_id(db: DbSession, match_id: int):
    match = db.get(Match, match_id)

    if match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Match not found")

    return match
@router.post("/create/{game}/{playtype}/{ladder}", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
def create_match(game: str, playtype: str, ladder: str, db: DbSession, user: CurrentUser):
    new_match = create_match_helper(game, playtype, ladder, db, user)
    db.commit()
    return new_match

@router.post("/submit")
def submit_active_match(db: DbSession, user: CurrentUser):
    active_match = db.scalar(
        select(Match)
        .where(
            Match.user_id == user.id,
            Match.status == MatchStatus.ACTIVE
        )
    )

    if active_match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active match!")

    enqueue_match_pre_submission(db, user.id, active_match.id)

    return {"message": "Submitted"}

@router.post("/skip", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
def skip_active_match(db: DbSession, user: CurrentUser):
    active_match = db.scalar(
        select(Match)
        .where(
            Match.user_id == user.id,
            Match.status == MatchStatus.ACTIVE
        )
        .with_for_update()
    )

    if active_match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active match!")

    active_match.status = MatchStatus.CANCELLED
    active_match.cancel_reason = CancelReason.NO_CHART
    active_match.end_time = datetime.now(timezone.utc)

    user.avoided_charts.append(UserAvoidedChart(chart_id=active_match.chart_id))

    db.flush()

    new_match = create_match_helper(active_match.game, active_match.playtype, active_match.ladder, db, user, [a.chart_id for a in user.avoided_charts])

    db.commit()

    return new_match

@router.get("/{user_id}/table", response_class=HTMLResponse)
def serve_user_table_index(db: DbSession, user_id: int):
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8-sig">
    <meta name="bmstable" content="table/header.json">
    <title> Arcadium Match Table</title>
</head>
<body>
    <p>Add this URL to your BMS Client's difficulty tables.</p>
</body>
</html>
"""

@router.get("/{user_id}/table/header.json")
def serve_header_table_data(db: DbSession, user_id: int):
    return {
        "name": "Arcadium Match",
        "symbol": "⚔",
        "data_url": f"data.json"
        }

@router.get("/{user_id}/table/data.json")
def serve_data_table_data(db: DbSession):
    return [{
        "md5": "7aee705ad2b6e16eb7d50d29dca5acb2",
        "sha256": "c9bf5cecbd61752832a02df8fc4f04064d09167adfa46615b98a2cc65d6c0fe1",
        "level": "EC",
        "title": "MASAMUNE (obj:LAPIS)",
        "artist": "NS-Factory"
    }]