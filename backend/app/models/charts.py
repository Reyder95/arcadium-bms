from sqlalchemy import ForeignKey, String, func, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

from app.models.base import Base

class Chart(Base):
    __tablename__ = "charts"

    chart_id: Mapped[str] = mapped_column(String, primary_key=True)
    song_id: Mapped[str | None] = mapped_column(String, index=True)
    md5: Mapped[str | None] = mapped_column(String(32), index=True)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    artist: Mapped[str | None]
    title: Mapped[str | None]
    sg_ec: Mapped[float | None]
    sg_hc: Mapped[float | None]
    game: Mapped[str] = mapped_column(String(16), index=True)
    playtype: Mapped[str] = mapped_column(String(8), index=True)

    table_levels: Mapped[list["ChartTableLevel"]] = relationship(back_populates="chart")
    ratings: Mapped[list["ChartRating"]] = relationship(back_populates="chart")


class ChartTableLevel(Base):
    __tablename__ = "chart_table_levels"

    chart_id: Mapped[str] = mapped_column(ForeignKey("charts.chart_id"), primary_key=True)
    table_icon: Mapped[str] = mapped_column(primary_key=True)
    table_level: Mapped[str]

    chart: Mapped[Chart] = relationship(back_populates="table_levels")

class ChartRating(Base):
    __tablename__ = "chart_ratings"

    chart_id: Mapped[str] = mapped_column(ForeignKey("charts.chart_id"), primary_key=True)
    ladder: Mapped[str] = mapped_column(String(8), primary_key=True)
    rating: Mapped[float]
    rd: Mapped[float]
    volatility: Mapped[float]
    games_played: Mapped[int] = mapped_column(default=0)
    wins: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )

    chart: Mapped[Chart] = relationship(back_populates="ratings")