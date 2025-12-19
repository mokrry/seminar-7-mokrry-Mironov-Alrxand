from sqlalchemy import func, case, distinct, cast, Float
from sqlalchemy.orm import Session
from sqlalchemy.sql import tuple_

from models import Country, Olympic, Player, Event, Result


def q1_birthyear_players_gold_2004(db: Session):
    """
    Для Олимпиады 2004: (год рождения, кол-во игроков, кол-во золотых медалей)
    Считаем игроков, которые вообще встречаются в results в событиях Олимпиады 2004.
    """
    birth_year = cast(func.extract("year", Player.birthdate), Integer := func.cast(1, int).__class__)  # трюк не нужен
    # ^ выше можно было бы проще, но в разных окружениях extract возвращает Decimal.
    # Поэтому сделаем проще ниже: cast(extract(..), Integer) через sqlalchemy.Integer:
    from sqlalchemy import Integer as SAInteger
    birth_year = cast(func.extract("year", Player.birthdate), SAInteger).label("birth_year")

    gold_count = func.sum(
        case((Result.medal == "GOLD", 1), else_=0)
    ).label("gold_medals")

    stmt = (
        db.query(
            birth_year,
            func.count(distinct(Player.player_id)).label("players_count"),
            gold_count,
        )
        .join(Result, Result.player_id == Player.player_id)
        .join(Event, Event.event_id == Result.event_id)
        .join(Olympic, Olympic.olympic_id == Event.olympic_id)
        .filter(Olympic.year == 2004)
        .group_by(birth_year)
        .order_by(birth_year)
    )
    return stmt.all()


def q2_individual_events_with_gold_tie(db: Session):
    """
    Все индивидуальные соревнования, где ничья по золоту:
    is_team_event = false и GOLD выдали >= 2 спортсменам.
    """
    stmt = (
        db.query(
            Event.event_id,
            Event.name,
            Event.olympic_id,
            func.count(Result.player_id).label("gold_winners"),
        )
        .join(Result, Result.event_id == Event.event_id)
        .filter(Event.is_team_event.is_(False))
        .filter(Result.medal == "GOLD")
        .group_by(Event.event_id, Event.name, Event.olympic_id)
        .having(func.count(Result.player_id) >= 2)
        .order_by(Event.olympic_id, Event.name)
    )
    return stmt.all()


def q3_players_with_any_medal_per_olympics(db: Session):
    """
    Все игроки, которые выиграли хотя бы одну медаль на одной олимпиаде.
    Вывести player_name и olympic_id.
    """
    stmt = (
        db.query(
            Player.name.label("player_name"),
            Olympic.olympic_id.label("olympic_id"),
        )
        .join(Result, Result.player_id == Player.player_id)
        .join(Event, Event.event_id == Result.event_id)
        .join(Olympic, Olympic.olympic_id == Event.olympic_id)
        .filter(Result.medal.in_(["GOLD", "SILVER", "BRONZE"]))
        .distinct()
        .order_by(Player.name, Olympic.olympic_id)
    )
    return stmt.all()


def q4_country_max_percent_vowel_names(db: Session):
    """
    В какой стране наибольший % игроков, чьё имя начинается с гласной.
    Гласные считаем по-английски: A E I O U (без Y).
    """
    vowels = ["a", "e", "i", "o", "u"]
    first_letter = func.lower(func.substr(Player.name, 1, 1))

    total_players = func.count(Player.player_id)
    vowel_players = func.sum(case((first_letter.in_(vowels), 1), else_=0))

    percent = (cast(vowel_players, Float) / cast(total_players, Float) * 100.0).label("percent_vowel")

    stmt = (
        db.query(
            Country.country_id,
            Country.name,
            percent,
            total_players.label("total_players"),
        )
        .join(Player, Player.country_id == Country.country_id)
        .group_by(Country.country_id, Country.name)
        .order_by(percent.desc())
    )

    return stmt.first()  # страна с максимальным %


def q5_syd2000_5_countries_min_team_medals_per_population(db: Session):
    """
    Для Олимпиады 2000: 5 стран с минимальным отношением:
    (кол-во групповых медалей) / (население)

    ВАЖНО: у team-ивентов в results по строке на каждого игрока.
    Чтобы НЕ считать одну командную медаль 4 раза,
    считаем DISTINCT (event_id, medal, country_id).
    """
    # Берём только SYD2000 (можно и Olympic.year == 2000)
    olympic_id_2000 = "SYD2000"

    team_medals_distinct = func.count(
        distinct(tuple_(Result.event_id, Result.medal, Player.country_id))
    ).label("team_medals")

    ratio = (cast(team_medals_distinct, Float) / cast(Country.population, Float)).label("medals_per_population")

    stmt = (
        db.query(
            Country.country_id,
            Country.name,
            Country.population,
            team_medals_distinct,
            ratio,
        )
        .join(Player, Player.country_id == Country.country_id)
        .join(Result, Result.player_id == Player.player_id)
        .join(Event, Event.event_id == Result.event_id)
        .filter(Event.olympic_id == olympic_id_2000)
        .filter(Event.is_team_event.is_(True))
        .filter(Result.medal.in_(["GOLD", "SILVER", "BRONZE"]))
        .group_by(Country.country_id, Country.name, Country.population)
        .having(team_medals_distinct > 0)  # чтобы не получить кучу стран с 0
        .order_by(ratio.asc())
        .limit(5)
    )
    return stmt.all()
