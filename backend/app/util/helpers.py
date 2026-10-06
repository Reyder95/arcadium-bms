from fastapi import status, HTTPException
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone

from app.db import DbSession
from app.util.dependencies import CurrentUser
from app.job.handlers import get_or_create_player_rating, get_player_rating
from app.job.enqueue import enqueue_tachi_seed, enqueue_match_final_check
from app.models import Chart, ChartRating, Match, PlayerRating
from app.util.enums import MatchStatus, MatchType, MatchResult

MATCH_DURATION = timedelta(minutes=12)

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

def create_match_helper(game: str, playtype: str, ladder: str, type: MatchType, elo: float | None, db: DbSession, user: CurrentUser, avoided_chart_ids: list[str] = []):
    rating_seed_key = f"{game}:{playtype}:{ladder}"

    if rating_seed_key not in user.rating_seeds and get_player_rating(db, user.id, game, playtype, ladder) is None:
        enqueue_tachi_seed(db, user.id)
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Your rating is still being set up. Try again in a few seconds."
        )

    seed = user.rating_seeds.get(rating_seed_key)
    elo_rating = seed["elo"] if seed else 100

    if ladder == "ec":
        elo_rating = elo_rating - 150

    if ladder == "hc":
        elo_rating = elo_rating - 300
    
    rating = get_or_create_player_rating(
        db,
        user.id, 
        ladder, 
        game, 
        playtype, 
        elo_rating, 
        seed_rd(seed["numScores"]) if seed else None
        )

    search_rating = rating.rating

    if (type == MatchType.CASUAL and elo is not None):
        search_rating = elo

    max_window = 300
    curr_window = 100
    window_increment = 50
    random_chart = None

    while curr_window <= max_window:
        random_chart = db.scalar(
            select(Chart)
            .join(ChartRating)
            .where(
                ChartRating.ladder == ladder,
                ChartRating.rating >= max(100, search_rating - curr_window),
                ChartRating.rating <= search_rating + curr_window,
                Chart.chart_id.not_in(avoided_chart_ids)
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
        type=type,
        search_elo=search_rating,
        playtype=playtype,
        player_mmr_before=rating.rating,
        player_display_before=rating.display_rating,
        chart_rating_before=chart_rating.rating,
        start_time=now,
        cutoff_time=now + MATCH_DURATION,
        )

    db.add(match)
    db.refresh(rating)

    enqueue_match_final_check(db, user.id, match.id, match.cutoff_time)

    return match

def get_active_match(db: DbSession, user: CurrentUser):
    active_match = db.scalar(
        select(Match)
        .where(
            Match.user_id == user.id,
            Match.status == MatchStatus.ACTIVE
        )
        .with_for_update()
    )

    return active_match

def get_active_match_by_userid(db: DbSession, user_id: int):
    active_match = db.scalar(
        select(Match)
        .where(
            Match.user_id == user_id,
            Match.status == MatchStatus.ACTIVE
        )
        .with_for_update()
    )

    return active_match

def get_standing(db, r, user_id):
    total = db.scalar(
        select(func.count())
        .select_from(PlayerRating)
        .where(
            PlayerRating.game == r.game,
            PlayerRating.playtype == r.playtype,
            PlayerRating.ladder == r.ladder
        )
    )

    rank = db.scalar(
        select(func.count())
        .select_from(PlayerRating)
        .where(
            PlayerRating.game == r.game,
            PlayerRating.playtype == r.playtype,
            PlayerRating.ladder == r.ladder,
            PlayerRating.display_rating > r.display_rating
        )
    ) + 1

    wins = db.scalar(
        select(func.count())
        .select_from(Match)
        .where(
            Match.user_id == user_id,
            Match.result == MatchResult.WIN,
            Match.type == MatchType.COMPETITIVE,
            Match.game == r.game,
            Match.playtype == r.playtype,
            Match.ladder == r.ladder
        )
    )

    losses = db.scalar(
        select(func.count())
        .select_from(Match)
        .where(
            Match.user_id == user_id,
            Match.result == MatchResult.LOSS,
            Match.type == MatchType.COMPETITIVE,
            Match.game == r.game,
            Match.playtype == r.playtype,
            Match.ladder == r.ladder
        )
    )

    return rank, total, wins, losses