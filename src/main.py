from __future__ import annotations

import os

from sqlalchemy import Float, case, distinct, func, select, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from models import Country, Event, Olympics, Player, Result


def make_engine() -> Engine:
    # Если запускаешь из Windows-хоста: обычно localhost:5444
    # Если запускаешь ИЗ контейнера в одной сети compose: host будет "olympics", порт 5432.
    db_url = os.environ.get(
        "DB_URL",
        "postgresql+psycopg2://olympics:olympics@localhost:5444/olympics",
    )
    return create_engine(db_url, future=True)


def q1_birth_year_stats_ath2004(session: Session):
    birth_year = func.extract("year", Player.birthdate).label("birth_year")
    gold_cnt = func.count(case((Result.medal == "GOLD", 1))).label("gold_medals")

    stmt = (
        select(
            birth_year,
            func.count(distinct(Player.player_id)).label("players"),
            gold_cnt,
        )
        .join(Result, Result.player_id == Player.player_id)
        .join(Event, Event.event_id == Result.event_id)
        .join(Olympics, Olympics.olympic_id == Event.olympic_id)
        .where(Olympics.olympic_id == "ATH2004")
        .group_by(birth_year)
        .order_by(birth_year)
    )
    return session.execute(stmt).all()


def q2_individual_events_with_gold_tie(session: Session):
    stmt = (
        select(
            Event.event_id,
            Event.name,
            Event.olympic_id,
            func.count(Result.player_id).label("gold_winners"),
        )
        .join(Result, Result.event_id == Event.event_id)
        .where(
            Event.is_team_event.is_(False),
            Result.medal == "GOLD",
        )
        .group_by(Event.event_id, Event.name, Event.olympic_id)
        .having(func.count(Result.player_id) >= 2)
        .order_by(Event.olympic_id, Event.event_id)
    )
    return session.execute(stmt).all()


def q3_players_with_any_medal_on_some_olympics(session: Session):
    stmt = (
        select(
            Player.player_id,
            Player.name,
            Olympics.olympic_id,
        )
        .join(Result, Result.player_id == Player.player_id)
        .join(Event, Event.event_id == Result.event_id)
        .join(Olympics, Olympics.olympic_id == Event.olympic_id)
        .where(Result.medal.in_(["GOLD", "SILVER", "BRONZE"]))
        .distinct()
        .order_by(Player.name, Olympics.olympic_id)
    )
    return session.execute(stmt).all()


def q4_country_with_max_vowel_name_pct(session: Session):
    first_letter = func.upper(func.substr(Player.name, 1, 1))
    is_vowel = case((first_letter.in_(["A", "E", "I", "O", "U"]), 1), else_=0)

    # доля (0..1)
    ratio = func.sum(is_vowel).cast(Float) / func.count(Player.player_id)
    pct = (ratio * 100.0).label("pct")

    stmt = (
        select(
            Country.country_id,
            Country.name,
            pct,
        )
        .join(Player, Player.country_id == Country.country_id)
        .group_by(Country.country_id, Country.name)
        .having(func.count(Player.player_id) > 0)
        .order_by(ratio.desc(), Country.country_id.asc())  # ratio DESC, чтобы брать максимум
        .limit(1)
    )
    return session.execute(stmt).one()


def q5_bottom5_team_medals_per_population_syd2000(session: Session):
    # считаем "групповые медали" как DISTINCT (country_id, event_id, medal) по командным событиям
    triples = (
        select(
            Player.country_id.label("country_id"),
            Result.event_id.label("event_id"),
            Result.medal.label("medal"),
        )
        .join(Player, Player.player_id == Result.player_id)
        .join(Event, Event.event_id == Result.event_id)
        .where(
            Event.olympic_id == "SYD2000",
            Event.is_team_event.is_(True),
            Result.medal.in_(["GOLD", "SILVER", "BRONZE"]),
        )
        .distinct()
        .subquery()
    )

    team_counts = (
        select(
            triples.c.country_id,
            func.count().label("team_medals"),
        )
        .group_by(triples.c.country_id)
        .subquery()
    )

    team_medals = func.coalesce(team_counts.c.team_medals, 0).label("team_medals")
    ratio = (team_medals.cast(Float) / Country.population.cast(Float)).label("ratio")

    stmt = (
        select(
            Country.country_id,
            Country.name,
            Country.population,
            team_medals,
            ratio,
        )
        .outerjoin(team_counts, team_counts.c.country_id == Country.country_id)
        .where(Country.population.is_not(None), Country.population > 0)
        .order_by(ratio.asc(), Country.name.asc())
        .limit(5)
    )
    return session.execute(stmt).all()


def main():
    engine = make_engine()
    with Session(engine) as session:
        print("Q1:", q1_birth_year_stats_ath2004(session)[:10], "...")
        print("Q2:", q2_individual_events_with_gold_tie(session)[:10], "...")
        print("Q3:", q3_players_with_any_medal_on_some_olympics(session)[:10], "...")
        print("Q4:", q4_country_with_max_vowel_name_pct(session))
        print("Q5:", q5_bottom5_team_medals_per_population_syd2000(session))


if __name__ == "__main__":
    main()
