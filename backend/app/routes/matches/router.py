from fastapi import APIRouter, status, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from typing import Annotated

from app.db import DbSession
from app.util.enums import CancelReason, MatchStatus, MatchResult, MatchType
from app.models import Match, UserAvoidedChart, User, ChartRating
from app.util.dependencies import CurrentUser
from app.util.helpers import create_match_helper, get_active_match, get_active_match_by_userid, calculate_pt_gain_and_loss
from app.job.enqueue import enqueue_match_pre_submission
from app.job.handlers import resolve_match
from app.ratings import GlickoRating, update

from app.schemas.match import MatchOut, MatchWithStakesOut

router = APIRouter(prefix="/match", tags=["match"])

@router.get("/{match_id}", response_model=MatchWithStakesOut, status_code=status.HTTP_200_OK)
def get_match_by_id(db: DbSession, match_id: int):
    match = db.get(Match, match_id)

    if match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Match not found")
    
    user = db.get(User, match.user_id)

    pt_gain, pt_loss = calculate_pt_gain_and_loss(user, match)

    base = MatchOut.model_validate(match)

    return MatchWithStakesOut(**base.model_dump(), potential_gain=pt_gain, potential_loss=pt_loss)

@router.post("/create", response_model=MatchWithStakesOut, status_code=status.HTTP_201_CREATED)
def create_match(game: str, playtype: str, ladder: str, db: DbSession, user: CurrentUser, elo: Annotated[float | None, Query(ge=100, le=2050)] = None, type: MatchType = MatchType.COMPETITIVE):
    active_match = get_active_match(db, user)

    if active_match is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have an active match!")
    new_match = create_match_helper(game, playtype, ladder, type, elo, db, user)
    db.commit()

    pt_gain, pt_loss = calculate_pt_gain_and_loss(user, new_match)

    base = MatchOut.model_validate(new_match)

    return MatchWithStakesOut(**base.model_dump(), potential_gain=pt_gain, potential_loss=pt_loss)

@router.post("/submit")
def submit_active_match(db: DbSession, user: CurrentUser):
    active_match = get_active_match(db, user)

    if active_match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active match!")

    job = enqueue_match_pre_submission(db, user.id, active_match.id)

    db.commit()

    return {"message": "Submitted", "job_id": job.id}

@router.post("/skip", response_model=MatchWithStakesOut, status_code=status.HTTP_201_CREATED)
def skip_active_match(db: DbSession, user: CurrentUser):
    active_match = get_active_match(db, user)

    if active_match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active match!")

    skip_limit_time = active_match.start_time + timedelta(minutes=0.5)

    if datetime.now(timezone.utc) > skip_limit_time:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not within the allotted time to skip match!")

    active_match.status = MatchStatus.CANCELLED
    active_match.cancel_reason = CancelReason.NO_CHART
    active_match.end_time = datetime.now(timezone.utc)

    user.avoided_charts.append(UserAvoidedChart(chart_id=active_match.chart_id))

    db.flush()

    new_match = create_match_helper(active_match.game, active_match.playtype, active_match.ladder, active_match.type, active_match.search_elo, db, user, [a.chart_id for a in user.avoided_charts])

    pt_gain, pt_loss = calculate_pt_gain_and_loss(user, new_match)

    db.commit()

    base = MatchOut.model_validate(new_match)

    return MatchWithStakesOut(**base.model_dump(), potential_gain=pt_gain, potential_loss=pt_loss)

@router.post("/forfeit", response_model=MatchWithStakesOut, status_code=status.HTTP_200_OK)
def forfeit_active_match(db: DbSession, user: CurrentUser):
    active_match = get_active_match(db, user)

    if active_match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active match!")

    pt_gain, pt_loss = calculate_pt_gain_and_loss(user, active_match)

    resolve_match(db, active_match.id, None)

    db.commit()

    base = MatchOut.model_validate(active_match)

    return MatchWithStakesOut(**base.model_dump(), potential_gain=pt_gain, potential_loss=pt_loss)

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
    user = db.get(User, user_id)

    if (user is None):
        raise HTTPException(status.HTTP_404_CONFLICT, "User not found!")
    
    return {
        "name": f"Arcadium Ladder: {user.username}",
        "symbol": "※",
        "data_url": f"data.json"
        }

@router.get("/{user_id}/table/data.json")
def serve_data_table_data(db: DbSession, user_id: int):

    chart_data = [{
        "md5": "0" * 32,
        "sha256": "0" * 64,
        "level": "User Has No Active Match!",
        "title": "No active match - Start one on Arcadium!",
        "artist": ""
    }]

    active_match = get_active_match_by_userid(db, user_id)

    if active_match is None:
        return chart_data

    ladder = "Easy Clear Ladder" if active_match.ladder == "ec" else "Hard Clear Ladder"

    chart_data = [{
        "md5": active_match.chart.md5,
        "sha256": active_match.chart.sha256,
        "level": f"{ladder}",
        "title": active_match.chart.title,
        "artist": active_match.chart.artist
    }]

    return chart_data