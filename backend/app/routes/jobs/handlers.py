from datetime import datetime, timezone, timedelta
from enum import StrEnum
from app.models.matches import MatchStatus, MatchResult
from app.models import ChartRating
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models import User, Match
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
GRACE_PERIOD = timedelta(minutes=2)

class ClearTypes(StrEnum):
    NO_PLAY = "NO PLAY"
    FAILED = "FAILED"
    ASSIST_CLEAR = "ASSIST CLEAR"
    EASY_CLEAR = "EASY CLEAR"
    CLEAR = "CLEAR"
    HARD_CLEAR = "HARD CLEAR"

LAMP_ORDER = [
    ClearTypes.NO_PLAY,
    ClearTypes.FAILED,
    ClearTypes.ASSIST_CLEAR,
    ClearTypes.EASY_CLEAR,
    ClearTypes.CLEAR,
    ClearTypes.HARD_CLEAR
]

LAMP_RANK = {lamp: i for i, lamp in enumerate(LAMP_ORDER)}

LADDER_REQUIREMENT = {
    "ec": ClearTypes.EASY_CLEAR,
    "hc": ClearTypes.HARD_CLEAR
}

def resolve_match(db, match_id: int, score: dict | None) -> dict:
    match = db.scalar(select(Match).where(Match.id == match_id).with_for_update())
    if match is None or match.status != MatchStatus.ACTIVE:
        return {"skipped": "already resolved"}

    won = score is not None
    player = get_player_rating(db, match.user_id, match.game, match.playtype, match.ladder)
    chart = get_chart_rating(db, match.chart_id, match.ladder)

    # calculate player rating via glicko2
    # calculate chart rating via glicko2

    # apply updates to player
    # apply updates to chart

    match.status = MatchStatus.RESOLVED
    match.result = MatchResult.WIN if won else MatchResult.LOSS
    match.end_time = datetime.now(timezone.utc)
    #match.player_mmr_after = player.rating
    #match.player.display_after = player.display_rating
    #match.chart_rating_after = chart.rating
    # score evidence fields maybe

    db.commit()

    return {"match_id": match.id, "result": match.result}

def meets_requirement(lamp: str, ladder: str) -> bool:
    return LAMP_RANK.get(lamp, -1) >= LAMP_RANK[LADDER_REQUIREMENT[ladder]]

def in_match_window(score, match) -> bool:
    added = tachi_time(score["timeAdded"])
    achieved = tachi_time(score["timeAchieved"])

    if added is None or not (match.start_time <= added <= match.cutoff_time + GRACE_PERIOD):
        return False
    if achieved is not None and not (match.start_time <= achieved <= match.cutoff_time):
        return False
    return True

def tachi_time(ms: int | None) -> datetime | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

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

def get_chart_rating(db: Session, chart_id: str, ladder: str) -> ChartRating:
    return db.scalar(
        select(ChartRating).where(
            ChartRating.chart_id == chart_id,
            ChartRating.ladder == ladder,
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

def match_end_check(db, job):
    match = db.get(Match, job.payload.get("matchId"))
    user = db.get(User, job.user_id)

    scores_call = tachi_get(f"/users/me/games/bms-{match.playtype}/scores/recent", user.tachi_api_key)

    recent_scores = scores_call["scores"]

    scores_in_window = [score for score in recent_scores if in_match_window(score, match)]

    scores_on_chart = [s for s in scores_in_window if s["chartID"] == match.chart_id]

    clears = [s for s in scores_on_chart if meets_requirement(s["scoreData"]["lamp"], match.ladder)]

    best_lamp = max(clears, key=lambda s: LAMP_RANK[s["scoreData"]["lamp"]]) if clears else None
    return resolve_match(db, match.id, best_lamp)

def match_pre_submission(db, job):
    match = db.get(Match, job.payload.get("matchId"))
    user = db.get(User, job.user_id)

    scores_call = tachi_get(f"/users/me/games/bms-{match.playtype}/scores/recent", user.tachi_api_key)

    recent_scores = scores_call["scores"]

    scores_in_window = [score for score in recent_scores if in_match_window(score, match)]

    scores_on_chart = [s for s in scores_in_window if s["chartID"] == match.chart_id]

    clears = [s for s in scores_on_chart if meets_requirement(s["scoreData"]["lamp"], match.ladder)]

    if len(clears) > 0:
        best_lamp = max(clears, key=lambda s: LAMP_RANK[s["scoreData"]["lamp"]]) if clears else None
        return resolve_match(db, match.id, best_lamp)

    newest = sorted(recent_scores, key=lambda s: s["timeAdded"], reverse=True)[:3]

    return {
        "payload": job.payload,
        "loaded_match_id": match.id,
        "match_start": match.start_time.isoformat(),
        "match_cutoff": match.cutoff_time.isoformat(),
        "newest_scores": [
            {
                "chartID": s["chartID"],
                "added": tachi_time(s["timeAdded"]).isoformat() if s["timeAdded"] else None,
                "achieved": tachi_time(s["timeAchieved"]).isoformat() if s["timeAchieved"] else None,
            }
            for s in newest
        ],
    }

HANDLERS = {
    "tachi_recent_score": tachi_recent_score,
    "tachi_rating": tachi_rating,
    "tachi_seed_profile": tachi_seed_profile,
    "match_end_check": match_end_check,
    "match_pre_submission": match_pre_submission
}