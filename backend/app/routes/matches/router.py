from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, ConfigDict, model_validator
from datetime import datetime

from app.db import DbSession
from app.models.matches import MatchResult, MatchStatus
from app.dependencies import CurrentUser
from app.routes.jobs.handlers import get_or_create_player_rating, get_player_rating
from app.routes.jobs.enqueue import enqueue_tachi_seed

router = APIRouter(prefix="/match", tags=["match"])

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

    game: str
    playtype: str
    user: UserPublicOut
    rating: PlayerRatingOut

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

    db.commit()
    db.refresh(rating)
    

    return {
        "game": game,
        "playtype": playtype,
        "user": user,
        "rating": rating
        }
