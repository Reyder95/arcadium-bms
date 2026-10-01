from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models import User
from app.tachi import tachi_get
from app.ratings import sieg_to_elo
from app.db import Session
from app.models import PlayerRating

class JobError(Exception):
    pass

DEFAULT_RATING = 850.0
DEFAULT_RD = 300.0
SEEDED_RD = 175.0
DEFAULT_VOLATILITY = 0.06

def check_tachi_key(user):
    if user is None or not user.tachi_api_key:
        raise JobError("No Bokutachi account linked!")

def save_seed_ratings(user, playtype: str, profile: dict) -> dict:
    ratings = profile.get("gameStats", {}).get("ratings", {})
    scores = profile.get("totalScores")

    seeds = {}

    value = ratings.get("sieglinde")

    if value is not None:
        seeds[f"bms:{playtype}:ec"] = { "elo": sieg_to_elo(value), "numScores": scores }
        seeds[f"bms:{playtype}:hc"] = { "elo": sieg_to_elo(value), "numScores": scores }
    else:
        seeds[f"bms:{playtype}:ec"] = None
        seeds[f"bms:{playtype}:hc"] = None

    user.rating_seeds = {**user.rating_seeds, **seeds}

    return seeds

def get_player_rating(db: Session, user_id: int, game: str, playtype: str, ladder: str) -> PlayerRating | None:
    return db.scalar(
        select(PlayerRating).where(
            PlayerRating.user_id == user_id,
            PlayerRating.game == game,
            PlayerRating.playtype == playtype,
            PlayerRating.ladder == ladder,
        )
    )

def get_or_create_player_rating(
        db: Session,
        user_id: int,
        ladder: str,
        game: str = "bms",
        playtype: str = "bms",
        seed_rating: float | None = None,
        seed_rd: float | None = None
) -> PlayerRating:
    existing = get_player_rating(db, user_id, game, playtype, ladder)

    if existing is not None:
        return existing

    rating = seed_rating if seed_rating is not None else DEFAULT_RATING
    rd = seed_rd if seed_rd is not None else DEFAULT_RD

    db.execute(
        insert(PlayerRating)
        .values(
            user_id=user_id,
            game=game,
            playtype=playtype,
            ladder=ladder,
            rating=rating,
            rd=rd,
            volatility=DEFAULT_VOLATILITY,
            display_rating=rating,
            placed=False,
            games_played=0
        )
        .on_conflict_do_nothing(
            index_elements=["user_id", "game", "playtype", "ladder"]
        )
    )

    return get_player_rating(db, user_id, game, playtype, ladder)

def tachi_recent_score(db, job):
    user = db.get(User, job.user_id)

    check_tachi_key(user)

    playtype = job.payload.get("playtype", "7k")

    data = tachi_get(f"/users/me/games/bms-{playtype}", user.tachi_api_key)

    return data["mostRecentScore"]

def tachi_rating(db, job):
    user = db.get(User, job.user_id)

    check_tachi_key(user)

    playtype = job.payload.get("playtype", "7k")

    data = tachi_get(f"/users/me/games/bms-{playtype}", user.tachi_api_key)

    return data["gameStats"]["ratings"]

def tachi_seed_profile(db, job):
    user = db.get(User, job.user_id)

    check_tachi_key(user)

    playtype = job.payload.get("playtype", "7k")

    profile = tachi_get(f"/users/me/games/bms-{playtype}", user.tachi_api_key)

    seeds = save_seed_ratings(user, playtype, profile)
    db.commit()
    return {"seeded": list(seeds)}

HANDLERS = {
    "tachi_recent_score": tachi_recent_score,
    "tachi_rating": tachi_rating,
    "tachi_seed_profile": tachi_seed_profile
}