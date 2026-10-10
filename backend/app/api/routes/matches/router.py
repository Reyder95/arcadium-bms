from fastapi import APIRouter, status, HTTPException, Query
from fastapi.responses import HTMLResponse
from datetime import datetime, timezone, timedelta
from typing import Annotated

from app.core.enums import CancelReason, MatchStatus, MatchType
from app.models import Match, UserAvoidedChart, User
from app.services.match import calculate_stakes, get_active_match_by_userid, create_match
from app.api.dependencies import CurrentUser, DbSession
from app.job.enqueue import enqueue_match_pre_submission, enqueue_match_forfeit
from app.core.errors import SeedPending

from app.schemas.match import MatchOut, MatchWithStakesOut

router = APIRouter(prefix="/match", tags=["match"])

@router.get("/{match_id}", response_model=MatchWithStakesOut, status_code=status.HTTP_200_OK)
def get_match_by_id(db: DbSession, match_id: int):
    match = db.get(Match, match_id)

    if match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Match not found")
    
    user = db.get(User, match.user_id)

    pt_gain, pt_loss = calculate_stakes(db, user, match)

    base = MatchOut.model_validate(match)

    return MatchWithStakesOut(**base.model_dump(), potential_gain=pt_gain, potential_loss=pt_loss)

@router.post("/create", response_model=MatchWithStakesOut, status_code=status.HTTP_201_CREATED)
def start_match(game: str, playtype: str, ladder: str, db: DbSession, user: CurrentUser, elo: Annotated[float | None, Query(ge=100, le=2050)] = None, type: MatchType = MatchType.COMPETITIVE):
    if not user.tachi_api_key or user.tachi_api_key == "":
        raise HTTPException(status.HTTP_409_CONFLICT, "No Tachi key found. Please set up your Tachi API key!")

    active_match = get_active_match_by_userid(db, user.id)

    if active_match is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have an active match!")

    try:
        new_match = create_match(db, user, game, playtype, ladder, type, elo)
    except SeedPending:
        db.commit()
        raise HTTPException(status.HTTP_409_CONFLICT, "Your rating is still being set up!")

    pt_gain, pt_loss = calculate_stakes(db, user, new_match)

    base = MatchOut.model_validate(new_match)

    db.commit()

    return MatchWithStakesOut(**base.model_dump(), potential_gain=pt_gain, potential_loss=pt_loss)

@router.post("/submit")
def submit_active_match(db: DbSession, user: CurrentUser):
    active_match = get_active_match_by_userid(db, user.id)

    if active_match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active match!")

    job = enqueue_match_pre_submission(db, user.id, active_match.id)

    db.commit()

    return {"message": "Submitted", "job_id": job.id}

@router.post("/skip", response_model=MatchWithStakesOut, status_code=status.HTTP_201_CREATED)
def skip_active_match(db: DbSession, user: CurrentUser):
    active_match = get_active_match_by_userid(db, user.id)

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

    new_match = create_match(db, user, active_match.game, active_match.playtype, active_match.ladder, active_match.type, active_match.search_elo, [a.chart_id for a in user.avoided_charts])

    pt_gain, pt_loss = calculate_stakes(db, user, new_match)

    db.commit()

    base = MatchOut.model_validate(new_match)

    return MatchWithStakesOut(**base.model_dump(), potential_gain=pt_gain, potential_loss=pt_loss)

@router.post("/forfeit", status_code=status.HTTP_200_OK)
def forfeit_active_match(db: DbSession, user: CurrentUser):
    active_match = get_active_match_by_userid(db, user.id)

    if active_match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active match!")

    if active_match.forfeited_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Match is already being forfeited!")

    active_match.forfeited_at = datetime.now(timezone.utc)

    enqueue_match_forfeit(db, user.id, active_match.id)

    db.commit()

    return {"message": "Submitted Forfeit!"}

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