import json
import os
from pathlib import Path
from datetime import datetime
import psycopg2
from dotenv import load_dotenv


# Пути к данным проекта

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SEASON_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "season_stats"
    / "season_2025_26.json"
)

PLAYER_PROFILES_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "season_stats"
    / "player_profiles.json"
)


# Настройки сезона

SEASON_ID = 25598
LEAGUE_ID = 501
SEASON_NAME = "2025/26"
LEAGUE_NAME = "Scottish Premiership"


# Ожидаемые значения

EXPECTED_MATCHES = 228
EXPECTED_TEAMS = 12
EXPECTED_PLAYERS = 439


# Переменные окружения

load_dotenv(PROJECT_ROOT / ".env")


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "football_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}


if not DB_CONFIG["password"]:
    raise ValueError("DB_PASSWORD не найден в .env")


# ID типов статистики игроков

PLAYER_STAT_TYPES = {
    # Common
    119: "minutes_played",
    118: "rating",
    120: "touches",
    27273: "possession_lost",

    # Attack
    52: "goals",
    79: "assists",
    42: "shots_total",
    86: "shots_on_target",
    41: "shots_off_target",
    580: "big_chances_created",
    581: "big_chances_missed",
    117: "key_passes",
    9706: "chances_created",
    108: "dribble_attempts",
    109: "successful_dribbles",
    110: "dribbled_past",
    98: "total_crosses",
    99: "accurate_crosses",
    124: "through_balls",
    125: "through_balls_won",
    51: "offsides",

    # Passing
    80: "passes",
    116: "accurate_passes",
    122: "long_balls",
    123: "long_balls_won",
    27269: "passes_in_final_third",
    27272: "backward_passes",

    # Defense
    78: "tackles",
    27267: "tackles_won",
    100: "interceptions",
    101: "clearances",
    105: "total_duels",
    106: "duels_won",
    1491: "duels_lost",
    27274: "aerials",
    107: "aerials_won",
    27266: "aerials_lost",
    27271: "ball_recovery",
    94: "dispossessed",

    # Discipline
    56: "fouls",
    96: "fouls_drawn",
    84: "yellowcards",
    83: "redcards",

    # Goalkeepers
    57: "saves",
    104: "saves_insidebox",
    103: "punches",
    584: "good_high_claim",
    1535: "goalkeeper_goals_conceded",

    # Penalties
    111: "penalties_scored",
    112: "penalties_missed",
    115: "penalties_won",
    114: "penalties_committed",
    113: "penalties_saved",
}


# ID типов статистики команд

TEAM_STAT_TYPES = {
    34: "corners",
    45: "ball_possession",
    52: "goals",
    79: "assists",
    1605: "successful_dribbles_percentage",
    84: "yellowcards",
    83: "redcards",
}


def load_json(path: Path):
    """Загружает данные из JSON-файла."""

    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_season_data() -> list[dict]:
    """Загружает и проверяет данные матчей сезона."""

    data = load_json(SEASON_PATH)

    if not isinstance(data, list):
        raise ValueError("season_2025_26.json должен содержать список матчей.")

    if len(data) != EXPECTED_MATCHES:
        raise ValueError(
            f"Ожидалось {EXPECTED_MATCHES} матчей, "
            f"получено {len(data)}."
        )

    return data


def load_player_profiles() -> dict[str, dict]:
    """Загружает сохранённые профили игроков."""

    data = load_json(PLAYER_PROFILES_PATH)

    if not isinstance(data, dict):
        raise ValueError(
            "player_profiles.json должен содержать объект "
            "с ключами player_id."
        )

    return data


def extract_teams(matches: list[dict]) -> dict[int, dict]:
    """Извлекает уникальные команды из участников матчей."""

    teams = {}

    for match in matches:
        for participant in match.get("participants", []):
            team_id = participant.get("id")

            if team_id is None:
                continue

            team = {
                "team_id": team_id,
                "name": participant.get("name"),
                "short_code": participant.get("short_code"),
            }

            if team_id in teams:
                existing = teams[team_id]

                if existing["name"] != team["name"]:
                    raise ValueError(
                        f"У команды {team_id} разные названия "
                        f"в разных матчах."
                    )

                if (
                    existing["short_code"]
                    and team["short_code"]
                    and existing["short_code"] != team["short_code"]
                ):
                    raise ValueError(
                        f"У команды {team_id} разные short_code."
                    )

            else:
                teams[team_id] = team

    return teams


def extract_player_ids(matches: list[dict]) -> set[int]:
    """Извлекает уникальные ID игроков из составов матчей."""

    player_ids = set()

    for match in matches:
        for lineup in match.get("lineups", []):
            player_id = lineup.get("player_id")

            if player_id is not None:
                player_ids.add(player_id)

    return player_ids


def validate_players(
    player_ids: set[int],
    profiles: dict[str, dict],
) -> None:
    """
    Check that every player participating in the season
    has a downloaded profile with a name.
    """

    missing_profiles = [
        player_id
        for player_id in sorted(player_ids)
        if str(player_id) not in profiles
    ]

    missing_names = [
        player_id
        for player_id in sorted(player_ids)
        if str(player_id) in profiles
        and not profiles[str(player_id)].get("name")
    ]

    if missing_profiles:
        raise ValueError(
            f"Недостаточно профилей игроков. "
            f"Отсутствуют профили: {len(missing_profiles)}."
        )

    if missing_names:
        raise ValueError(
            f"У {len(missing_names)} профилей отсутствует name."
        )


def validate_matches(
    matches: list[dict],
    team_ids: set[int],
) -> None:
    """Проверяет связи и основные данные матчей."""

    match_ids = set()

    for match in matches:
        match_id = match.get("id")

        if match_id is None:
            raise ValueError("Обнаружен матч без id.")

        if match_id in match_ids:
            raise ValueError(
                f"Обнаружен дубликат match_id={match_id}."
            )

        match_ids.add(match_id)

        if match.get("season_id") != SEASON_ID:
            raise ValueError(
                f"Матч {match_id} относится не к сезону {SEASON_ID}."
            )

        if not match.get("starting_at"):
            raise ValueError(
                f"У матча {match_id} отсутствует starting_at."
            )

        participants = match.get("participants", [])

        if len(participants) != 2:
            raise ValueError(
                f"Матч {match_id} должен иметь ровно "
                f"2 участников, получено {len(participants)}."
            )

        home_team_id = None
        away_team_id = None

        for participant in participants:
            team_id = participant.get("id")
            location = participant.get("meta", {}).get("location")

            if team_id not in team_ids:
                raise ValueError(
                    f"Матч {match_id} содержит неизвестную "
                    f"команду {team_id}."
                )

            if location == "home":
                home_team_id = team_id
            elif location == "away":
                away_team_id = team_id

        if home_team_id is None or away_team_id is None:
            raise ValueError(
                f"Не удалось определить home/away для матча {match_id}."
            )

        if home_team_id == away_team_id:
            raise ValueError(
                f"Матч {match_id} содержит одну и ту же "
                f"команду дома и в гостях."
            )


def parse_datetime(value: str) -> datetime:
    """Преобразует дату Sportmonks в datetime Python."""

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(
            f"Некорректный starting_at: {value}"
        ) from error


def get_stat_type_id(stat: dict) -> int | None:
    """Извлекает ID типа статистики Sportmonks."""

    # Current Sportmonks fixture statistics contain type_id
    # directly in the statistic object.
    type_id = stat.get("type_id")

    if type_id is not None:
        return type_id

    # Резервный вариант для ответа со вложенным объектом type.
    stat_type = stat.get("type")

    if isinstance(stat_type, dict):
        return stat_type.get("id")

    if isinstance(stat_type, int):
        return stat_type

    return None


def get_stat_value(stat: dict):
    """Извлекает значение статистики Sportmonks."""

    # Current Sportmonks structure:
    # "data": {
    #     "value": ...
    # }
    data = stat.get("data")

    if isinstance(data, dict):
        return data.get("value")

    # Резервный вариант для альтернативной структуры ответа.
    value = stat.get("value")

    if isinstance(value, dict):
        return value.get("value")

    return value


def convert_numeric(value):
    """Преобразует значение статистики Sportmonks в число."""

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        try:
            number = float(value)

            if number.is_integer():
                return int(number)

            return number

        except ValueError:
            raise ValueError(
                f"Не удалось преобразовать значение статистики: {value}"
            )

    raise ValueError(
        f"Неизвестный формат значения статистики: {value!r}"
    )


def extract_player_stats(lineup: dict) -> dict:
    """Извлекает выбранную статистику игрока из одного состава."""

    stats = {
        column: None
        for column in PLAYER_STAT_TYPES.values()
    }

    for detail in lineup.get("details", []):
        type_id = get_stat_type_id(detail)

        column = PLAYER_STAT_TYPES.get(type_id)

        if column is None:
            continue

        value = get_stat_value(detail)

        stats[column] = convert_numeric(value)

    return stats


def extract_team_stats(match: dict) -> list[dict]:
    """Извлекает выбранную статистику команд из одного матча."""

    result = []

    for statistic in match.get("statistics", []):
        team_id = (
            statistic.get("participant_id")
            or statistic.get("team_id")
        )

        if team_id is None:
            continue

        type_id = get_stat_type_id(statistic)

        column = TEAM_STAT_TYPES.get(type_id)

        if column is None:
            continue

        value = convert_numeric(get_stat_value(statistic))

        result.append(
            {
                "team_id": team_id,
                "column": column,
                "value": value,
            }
        )

    return result


def prepare_team_match_rows(
    matches: list[dict],
) -> list[dict]:
    """Подготавливает строки для таблицы team_match."""

    rows = []

    for match in matches:
        match_id = match["id"]

        stats_by_team = {}

        for statistic in extract_team_stats(match):
            team_id = statistic["team_id"]
            column = statistic["column"]
            value = statistic["value"]

            stats_by_team.setdefault(team_id, {})

            if column in stats_by_team[team_id]:
                raise ValueError(
                    f"Дубликат team statistic: "
                    f"match_id={match_id}, "
                    f"team_id={team_id}, "
                    f"stat={column}."
                )

            stats_by_team[team_id][column] = value

        for participant in match.get("participants", []):
            team_id = participant["id"]

            row = {
                "match_id": match_id,
                "team_id": team_id,
                "corners": None,
                "ball_possession": None,
                "goals": None,
                "assists": None,
                "successful_dribbles_percentage": None,
                "yellowcards": None,
                "redcards": None,
            }

            row.update(stats_by_team.get(team_id, {}))

            rows.append(row)

    return rows



def prepare_player_match_rows(
    matches: list[dict],
) -> list[dict]:
    """Подготавливает строки player_match только для сыгравших игроков."""

    rows = []
    skipped_without_player_id = 0
    skipped_without_minutes = 0

    for match in matches:
        match_id = match["id"]

        for lineup in match.get("lineups", []):
            player_id = lineup.get("player_id")
            team_id = lineup.get("team_id")

            if player_id is None:
                skipped_without_player_id += 1
                continue

            if team_id is None:
                raise ValueError(
                    f"Игрок {player_id} в матче {match_id} "
                    f"не содержит team_id."
                )

            stats = extract_player_stats(lineup)

            minutes_played = stats["minutes_played"]

            # player_match содержит только игроков,
            # которые реально вышли на поле.
            if minutes_played is None or minutes_played <= 0:
                skipped_without_minutes += 1
                continue

            row = {
                "player_id": player_id,
                "match_id": match_id,
                "team_id": team_id,
                "position_id": lineup.get("position_id"),
            }

            row.update(stats)

            rows.append(row)

    print(
        f"Пропущено lineup без player_id: "
        f"{skipped_without_player_id}"
    )

    print(
        f"Пропущено игроков без игрового времени: "
        f"{skipped_without_minutes}"
    )

    return rows


def connect_to_database():
    """Создаёт подключение к PostgreSQL."""

    return psycopg2.connect(**DB_CONFIG)


def insert_league(cursor) -> None:
    """Загружает данные лиги."""

    cursor.execute(
        """
        INSERT INTO leagues (
            league_id,
            name
        )
        VALUES (%s, %s)
        ON CONFLICT (league_id)
        DO UPDATE SET
            name = EXCLUDED.name
        """,
        (LEAGUE_ID, LEAGUE_NAME),
    )


def insert_season(cursor) -> None:
    """Загружает данные сезона."""

    cursor.execute(
        """
        INSERT INTO seasons (
            season_id,
            league_id,
            name
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (season_id)
        DO UPDATE SET
            league_id = EXCLUDED.league_id,
            name = EXCLUDED.name
        """,
        (SEASON_ID, LEAGUE_ID, SEASON_NAME),
    )


def insert_teams(
    cursor,
    teams: dict[int, dict],
) -> None:
    """Загружает команды."""

    query = """
        INSERT INTO teams (
            team_id,
            name,
            short_code
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (team_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            short_code = EXCLUDED.short_code
    """

    for team in teams.values():
        cursor.execute(
            query,
            (
                team["team_id"],
                team["name"],
                team["short_code"],
            ),
        )


def insert_players(
    cursor,
    player_ids: set[int],
    profiles: dict[str, dict],
) -> None:
    """Загружает профили игроков."""

    query = """
        INSERT INTO players (
            player_id,
            name,
            date_of_birth,
            height,
            weight,
            nationality
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (player_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            date_of_birth = EXCLUDED.date_of_birth,
            height = EXCLUDED.height,
            weight = EXCLUDED.weight,
            nationality = EXCLUDED.nationality
    """

    for player_id in sorted(player_ids):
        profile = profiles[str(player_id)]

        height = profile.get("height")
        weight = profile.get("weight")

        # Sportmonks uses 0 when the player's physical data is unknown.
        # Store unknown values as NULL instead of violating DB constraints.
        if height == 0:
            height = None

        if weight == 0:
            weight = None

        cursor.execute(
            query,
            (
                player_id,
                profile["name"],
                profile.get("date_of_birth"),
                height,
                weight,
                profile.get("nationality"),
            ),
        )


def insert_matches(
    cursor,
    matches: list[dict],
) -> None:
    """Загружает матчи."""

    query = """
        INSERT INTO matches (
            match_id,
            home_team_id,
            away_team_id,
            starting_at,
            season_id,
            round_id,
            venue_id,
            state_id,
            result_info
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (match_id)
        DO UPDATE SET
            home_team_id = EXCLUDED.home_team_id,
            away_team_id = EXCLUDED.away_team_id,
            starting_at = EXCLUDED.starting_at,
            season_id = EXCLUDED.season_id,
            round_id = EXCLUDED.round_id,
            venue_id = EXCLUDED.venue_id,
            state_id = EXCLUDED.state_id,
            result_info = EXCLUDED.result_info
    """

    for match in matches:
        home_team_id = None
        away_team_id = None

        for participant in match.get("participants", []):
            location = participant.get("meta", {}).get("location")

            if location == "home":
                home_team_id = participant["id"]
            elif location == "away":
                away_team_id = participant["id"]

        cursor.execute(
            query,
            (
                match["id"],
                home_team_id,
                away_team_id,
                parse_datetime(match["starting_at"]),
                match["season_id"],
                match.get("round_id"),
                match.get("venue_id"),
                match.get("state_id"),
                match.get("result_info"),
            ),
        )


def insert_team_match(
    cursor,
    rows: list[dict],
) -> None:
    """Загружает статистику команд в матчах."""

    query = """
        INSERT INTO team_match (
            match_id,
            team_id,
            corners,
            ball_possession,
            goals,
            assists,
            successful_dribbles_percentage,
            yellowcards,
            redcards
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (match_id, team_id)
        DO UPDATE SET
            corners = EXCLUDED.corners,
            ball_possession = EXCLUDED.ball_possession,
            goals = EXCLUDED.goals,
            assists = EXCLUDED.assists,
            successful_dribbles_percentage =
                EXCLUDED.successful_dribbles_percentage,
            yellowcards = EXCLUDED.yellowcards,
            redcards = EXCLUDED.redcards
    """

    for row in rows:
        cursor.execute(
            query,
            (
                row["match_id"],
                row["team_id"],
                row["corners"],
                row["ball_possession"],
                row["goals"],
                row["assists"],
                row["successful_dribbles_percentage"],
                row["yellowcards"],
                row["redcards"],
            ),
        )


def insert_player_match(
    cursor,
    rows: list[dict],
) -> None:
    """Загружает статистику игроков в матчах."""

    columns = [
        "player_id",
        "match_id",
        "team_id",
        "position_id",
        *PLAYER_STAT_TYPES.values(),
    ]

    placeholders = ", ".join(["%s"] * len(columns))

    query = f"""
        INSERT INTO player_match (
            {", ".join(columns)}
        )
        VALUES ({placeholders})
        ON CONFLICT (player_id, match_id)
        DO UPDATE SET
            team_id = EXCLUDED.team_id,
            position_id = EXCLUDED.position_id,
            {", ".join(
                f"{column} = EXCLUDED.{column}"
                for column in PLAYER_STAT_TYPES.values()
            )}
    """

    for row in rows:
        values = [row.get(column) for column in columns]

        cursor.execute(query, values)


def validate_prepared_data(
    matches: list[dict],
    teams: dict[int, dict],
    player_ids: set[int],
    team_match_rows: list[dict],
    player_match_rows: list[dict],
) -> None:
    """Проверяет подготовленные данные перед изменением базы данных."""

    team_ids = set(teams)

    if len(teams) != EXPECTED_TEAMS:
        raise ValueError(
            f"Ожидалось {EXPECTED_TEAMS} команд, "
            f"получено {len(teams)}."
        )

    if len(player_ids) != EXPECTED_PLAYERS:
        raise ValueError(
            f"Ожидалось {EXPECTED_PLAYERS} игроков, "
            f"получено {len(player_ids)}."
        )

    expected_team_match_rows = len(matches) * 2

    if len(team_match_rows) != expected_team_match_rows:
        raise ValueError(
            f"Ожидалось {expected_team_match_rows} строк team_match, "
            f"получено {len(team_match_rows)}."
        )

    seen_team_matches = set()

    for row in team_match_rows:
        key = (row["match_id"], row["team_id"])

        if key in seen_team_matches:
            raise ValueError(
                f"Дубликат team_match: {key}"
            )

        seen_team_matches.add(key)

        if row["team_id"] not in team_ids:
            raise ValueError(
                f"team_match содержит неизвестную команду "
                f"{row['team_id']}."
            )

    seen_player_matches = set()

    for row in player_match_rows:
        key = (row["player_id"], row["match_id"])

        if key in seen_player_matches:
            raise ValueError(
                f"Дубликат player_match: {key}"
            )

        seen_player_matches.add(key)

        if row["player_id"] not in player_ids:
            raise ValueError(
                f"player_match содержит неизвестного игрока "
                f"{row['player_id']}."
            )

        if row["team_id"] not in team_ids:
            raise ValueError(
                f"player_match содержит неизвестную команду "
                f"{row['team_id']}."
            )


def print_summary(
    matches: list[dict],
    teams: dict[int, dict],
    player_ids: set[int],
    team_match_rows: list[dict],
    player_match_rows: list[dict],
) -> None:
    """Выводит итог ETL-процесса."""

    print()
    print("Данные подготовлены.")
    print()
    print(f"Матчей:              {len(matches)}")
    print(f"Команд:              {len(teams)}")
    print(f"Игроков:             {len(player_ids)}")
    print(f"Строк team_match:    {len(team_match_rows)}")
    print(f"Строк player_match:  {len(player_match_rows)}")
    print()


def main() -> None:
    print("Загружаем исходные данные...")

    matches = load_season_data()
    profiles = load_player_profiles()

    print(f"Матчей загружено: {len(matches)}")
    print(f"Профилей игроков: {len(profiles)}")

    print("Извлекаем команды...")
    teams = extract_teams(matches)

    print("Извлекаем игроков...")
    player_ids = extract_player_ids(matches)

    print("Проверяем профили игроков...")
    validate_players(player_ids, profiles)

    print("Проверяем матчи...")
    validate_matches(matches, set(teams))

    print("Подготавливаем team_match...")
    team_match_rows = prepare_team_match_rows(matches)

    print("Подготавливаем player_match...")
    player_match_rows = prepare_player_match_rows(matches)

    print("Проверяем подготовленные данные...")
    validate_prepared_data(
        matches,
        teams,
        player_ids,
        team_match_rows,
        player_match_rows,
    )

    print_summary(
        matches,
        teams,
        player_ids,
        team_match_rows,
        player_match_rows,
    )

    print("Подключаемся к PostgreSQL...")

    connection = connect_to_database()

    try:
        with connection:
            with connection.cursor() as cursor:
                print("Загружаем league...")
                insert_league(cursor)

                print("Загружаем season...")
                insert_season(cursor)

                print("Загружаем teams...")
                insert_teams(cursor, teams)

                print("Загружаем players...")
                insert_players(cursor, player_ids, profiles)

                print("Загружаем matches...")
                insert_matches(cursor, matches)

                print("Загружаем team_match...")
                insert_team_match(cursor, team_match_rows)

                print("Загружаем player_match...")
                insert_player_match(cursor, player_match_rows)

        print()
        print("Загрузка завершена успешно.")

    except Exception:
        print()
        print("Ошибка при загрузке. Транзакция отменена.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
