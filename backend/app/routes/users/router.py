from fastapi import APIRouter

from app.db import DbSession
from app.util.helpers import get_standing, get_active_match_by_userid
from app.util.dependencies import CurrentUser
from app.schemas.match import MatchOut


from app.schemas.auth import UserRatingOut


router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/ratings", response_model=list[UserRatingOut])
def get_user_ratings(db: DbSession, user: CurrentUser):
    results = []
    
    for rating in user.ratings:
        rank, total, wins, losses = get_standing(db, rating, user.id)

        results.append({
            "game": rating.game,
            "playtype": rating.playtype,
            "ladder": rating.ladder,
            "display_rating": rating.display_rating,
            "placed": rating.placed,
            "games_played": rating.games_played,
            "rank": rank,
            "total": total,
            "wins": wins,
            "losses": losses
        })

    return results

@router.get("/me/ratings/{game}/{playtype}/{ladder}", response_model=list[UserRatingOut])
def get_user_rating_filtered(game: str, playtype: str, ladder: str, db: DbSession, user: CurrentUser):
    results = []
    
    for rating in user.ratings:

        if rating.game == game and rating.playtype == playtype and rating.ladder == ladder:
            rank, total, wins, losses = get_standing(db, rating, user.id)

            results.append({
                "game": rating.game,
                "playtype": rating.playtype,
                "ladder": rating.ladder,
                "display_rating": rating.display_rating,
                "placed": rating.placed,
                "games_played": rating.games_played,
                "rank": rank,
                "total": total,
                "wins": wins,
                "losses": losses
            })

    return results



@router.get("/me/can-queue")
def can_queue(user: CurrentUser):
    able = False

    if user.tachi_api_key != "" and user.tachi_api_key:
        able = True

    return {
        "can_queue": able
    }

@router.get("/me/active-match", response_model=MatchOut | None)
def get_user_active_match(db: DbSession, user: CurrentUser):
    return get_active_match_by_userid(db, user.id)