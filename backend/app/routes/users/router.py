from fastapi import APIRouter

from app.db import DbSession
from app.util.helpers import get_standing
from app.util.dependencies import CurrentUser


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