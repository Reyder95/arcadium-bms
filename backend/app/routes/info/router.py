from fastapi import APIRouter
from app.ratings import TIERS

router = APIRouter(prefix="/info", tags=["info"])

@router.get("/tiers")
def get_rating_tiers():
    return TIERS