from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, ConfigDict, model_validator
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func

from app.db import DbSession
from app.models.matches import MatchResult, MatchStatus
from app.models import Chart, ChartRating, Match
from app.dependencies import CurrentUser
from app.routes.jobs.handlers import get_or_create_player_rating, get_player_rating
from app.routes.jobs.enqueue import enqueue_tachi_seed, enqueue_match_final_check, enqueue_match_pre_submission

router = APIRouter(prefix="/match", tags=["match"])

MATCH_DURATION = timedelta(minutes=12)

class UserPublicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str

class TableLevelsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table_icon: str
    table_level: str

class ChartRatingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rating: float
    ladder: str
    rd: float
    volatility: float
    games_played: int
    wins: int

class ChartPublicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chart_id: str
    song_id: str | None
    md5: str | None
    sha256: str | None
    artist: str | None
    title: str | None
    subtitle: str | None
    table_levels: list[TableLevelsOut]
    ratings: list[ChartRatingsOut]


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: UserPublicOut
    chart: ChartPublicOut
    rating_change: float | None
    ladder: str
    game: str
    playtype: str
    result: MatchResult | None
    status: MatchStatus
    cancel_reason: str | None
    player_display_before: float | None
    player_display_after: float | None
    chart_rating_before: float | None
    chart_rating_after: float | None
    start_time: datetime
    cutoff_time: datetime
    end_time: datetime | None

    @model_validator(mode="after")
    def keep_only_match_ladder(self):
        self.chart.ratings = [r for r in self.chart.ratings if r.ladder == self.ladder]
        return self

class PlayerRatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ladder: str
    display_rating: float
    placed: bool
    games_played: int

class CreateMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match: MatchOut

def seed_rd(num_scores: int | None) -> float:
    if not num_scores:
        return 300.0
    if num_scores < 50:
        return 250.0
    if num_scores < 300:
        return 200.0
    if num_scores < 1000:
        return 160.0
    return 130.0

@router.get("/{match_id}", response_model=MatchOut, status_code=status.HTTP_200_OK)
def get_match_by_id(db: DbSession, match_id: int):
    match = db.get(Match, match_id)

    if match is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Match not found")

    return match
@router.post("/create/{game}/{playtype}/{ladder}", response_model=CreateMatchOut, status_code=status.HTTP_201_CREATED)
def create_match(game: str, playtype: str, ladder: str, db: DbSession, user: CurrentUser):

    rating_seed_key = f"{game}:{playtype}:{ladder}"

    if rating_seed_key not in user.rating_seeds and get_player_rating(db, user.id, game, playtype, ladder) is None:
        enqueue_tachi_seed(db, user.id)
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Your rating is still being set up. Try again in a few seconds."
        )

    seed = user.rating_seeds.get(rating_seed_key)
    
    rating = get_or_create_player_rating(
        db,
        user.id, 
        ladder, 
        game, 
        playtype, 
        seed["elo"] if seed else None, 
        seed_rd(seed["numScores"]) if seed else None
        )

    max_window = 250
    curr_window = 100
    window_increment = 50
    random_chart = None

    while curr_window <= max_window:
        random_chart = db.scalar(
            select(Chart)
            .join(ChartRating)
            .where(
                ChartRating.ladder == ladder,
                ChartRating.rating >= max(100, rating.rating - curr_window),
            ChartRating.rating <= rating.rating + curr_window
            ).order_by(func.random())
            .limit(1)
        )

        if random_chart is None:
            curr_window += window_increment
        else:
            break

    if random_chart is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "No charts available near your rating right now."
        )

    chart_rating = next((r for r in random_chart.ratings if r.ladder == ladder), None)

    now = datetime.now(timezone.utc)

    match = Match(
        user_id=user.id, 
        chart_id=random_chart.chart_id, 
        ladder=ladder, 
        game=game, 
        playtype=playtype,
        player_mmr_before=rating.rating,
        player_display_before=rating.display_rating,
        chart_rating_before=chart_rating.rating,
        start_time=now,
        cutoff_time=now + MATCH_DURATION,
        )

    db.add(match)
    db.commit()
    db.refresh(rating)

    enqueue_match_final_check(db, user.id, match.id, match.cutoff_time)
    

    return {
        "match": match
        }

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