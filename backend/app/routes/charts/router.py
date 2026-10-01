from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session

from app.db import get_db
from app.models import Chart, ChartRating, ChartTableLevel

router = APIRouter(prefix="/chart", tags=["chart"])

class ChartLevelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table_icon: str
    table_level: str

class ChartRatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ladder: str
    rating: float
    rd: float
    games_played: int

class ChartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chart_id: str
    title: str | None
    artist: str | None
    sg_ec: float | None
    sg_hc: float | None
    ratings: list[ChartRatingOut]
    table_levels: list[ChartLevelOut]

@router.get("", response_model=list[ChartOut])
def get_charts(
    db: Session = Depends(get_db),
    ladder: Annotated[str, Query(pattern="^(ec|hc)$")] = "ec",
    min_rating: float | None = None,
    max_rating: float | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0
):
    stmt = (
        select(Chart)
        .join(ChartRating, ChartRating.chart_id == Chart.chart_id)
        .where(ChartRating.ladder == ladder)
        .options(selectinload(Chart.ratings), selectinload(Chart.table_levels))
    )

    if min_rating is not None:
        stmt = stmt.where(ChartRating.rating >= min_rating)
    if max_rating is not None:
        stmt = stmt.where(ChartRating.rating <= max_rating)

    stmt = stmt.order_by(ChartRating.rating).limit(limit).offset(offset)
    return db.scalars(stmt).all()