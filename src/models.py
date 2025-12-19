from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Country(Base):
    __tablename__ = "countries"

    country_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    area_sqkm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    population: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    players: Mapped[List["Player"]] = relationship(back_populates="country")
    olympics: Mapped[List["Olympics"]] = relationship(back_populates="country")


class Olympics(Base):
    __tablename__ = "olympics"

    olympic_id: Mapped[str] = mapped_column(String, primary_key=True)
    country_id: Mapped[str] = mapped_column(ForeignKey("countries.country_id"))
    city: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)
    startdate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    enddate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    country: Mapped["Country"] = relationship(back_populates="olympics")
    events: Mapped[List["Event"]] = relationship(back_populates="olympics")


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    country_id: Mapped[str] = mapped_column(ForeignKey("countries.country_id"))
    birthdate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    country: Mapped["Country"] = relationship(back_populates="players")
    results: Mapped[List["Result"]] = relationship(back_populates="player")


class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    eventtype: Mapped[str] = mapped_column(String)
    olympic_id: Mapped[str] = mapped_column(ForeignKey("olympics.olympic_id"))
    is_team_event: Mapped[bool] = mapped_column(Boolean)
    num_players_in_team: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_noted_in: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    olympics: Mapped["Olympics"] = relationship(back_populates="events")
    results: Mapped[List["Result"]] = relationship(back_populates="event")


class Result(Base):
    __tablename__ = "results"

    # В датасете обычно уникальна пара (event_id, player_id)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.event_id"), primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"), primary_key=True)

    medal: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # GOLD/SILVER/BRONZE или NULL
    result: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    player: Mapped["Player"] = relationship(back_populates="results")
    event: Mapped["Event"] = relationship(back_populates="results")
