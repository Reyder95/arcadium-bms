from fastapi import APIRouter

from app.ratings import TIERS
from app.schemas.info import TierOut

router = APIRouter(prefix="/info", tags=["info"])

@router.get("/tiers", response_model=list[TierOut])
def get_rating_tiers():
    tiers = []

    for tier in TIERS:
        tiers.append(TierOut(name=tier[0], floor=tier[1]))

    return tiers