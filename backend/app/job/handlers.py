from datetime import datetime, timezone

from app.models import User, Match
from app.core.enums import ClearTypes
from app.services.tachi import tachi_get, get_recent_scores
from app.services.match import scores_for_match
from app.ratings import sieg_to_elo
from app.logic.match import LAMP_RANK, choose_best_score, lamp_counts_as_win
from app.services.match import resolve_match, get_best_score_for_match

class JobError(Exception):
    pass

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
        print(seeds)
    else:
        seeds[f"bms:{playtype}:ec"] = None
        seeds[f"bms:{playtype}:hc"] = None

    user.rating_seeds = {**user.rating_seeds, **seeds}

    return seeds

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

    best_score = get_best_score_for_match(user, match)

    if best_score is not None:
        won = lamp_counts_as_win(ClearTypes(best_score["scoreData"]["lamp"]))
    else:
        won = False

    return resolve_match(db, match.id, won, best_score)

def match_pre_submission(db, job):
    match = db.get(Match, job.payload.get("matchId"))
    user = db.get(User, job.user_id)

    best_score = get_best_score_for_match(user, match)

    if best_score is None:
        return {"match_id": match.id, "result": match.result}

    won = lamp_counts_as_win(ClearTypes(best_score["scoreData"]["lamp"]), match.ladder)

    if won:
        return resolve_match(db, match.id, won, best_score)
    return {"match_id": match.id, "result": match.result}

def match_forfeit(db, job):
    match: Match = db.get(Match, job.payload.get("matchId"))
    user: User = db.get(User, job.user_id)

    best_score = get_best_score_for_match(user, match)
    won = False

    return resolve_match(db, match.id, won, best_score)

HANDLERS = {
    "tachi_recent_score": tachi_recent_score,
    "tachi_rating": tachi_rating,
    "tachi_seed_profile": tachi_seed_profile,
    "match_end_check": match_end_check,
    "match_pre_submission": match_pre_submission,
    "match_forfeit": match_forfeit
}