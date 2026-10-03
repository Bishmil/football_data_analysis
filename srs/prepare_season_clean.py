import json
from pathlib import Path


# Пути к данным проекта

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SEASON_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "season_stats"
    / "season_2025_26.json"
)


# Ожидаемые значения для сезона 2025/26

EXPECTED_MATCHES = 228
EXPECTED_TEAMS = 12
EXPECTED_PLAYERS = 439
EXPECTED_SEASON_ID = 25598


def load_json(path: Path) -> list[dict]:
    """Загружает данные сезона из JSON-файла."""

    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Корень JSON должен содержать список матчей.")

    return data


def extract_teams(matches: list[dict]) -> dict[int, dict]:
    """Извлекает уникальные команды из участников матчей."""

    teams = {}

    for match in matches:
        for participant in match.get("participants", []):
            team_id = participant.get("id")

            if team_id is None:
                continue

            if team_id not in teams:
                teams[team_id] = {
                    "team_id": team_id,
                    "name": participant.get("name"),
                    "short_code": participant.get("short_code"),
                }

    return teams


def extract_players(matches: list[dict]) -> set[int]:
    """Извлекает уникальные ID игроков из составов матчей."""

    player_ids = set()

    for match in matches:
        for lineup in match.get("lineups", []):
            player_id = lineup.get("player_id")

            if player_id is not None:
                player_ids.add(player_id)

    return player_ids


def validate_matches(matches: list[dict]) -> None:
    """Проверяет базовую корректность данных матчей."""

    if len(matches) != EXPECTED_MATCHES:
        raise ValueError(
            f"Ожидалось {EXPECTED_MATCHES} матчей, "
            f"получено {len(matches)}."
        )

    match_ids = []

    for match in matches:
        match_id = match.get("id")

        if match_id is None:
            raise ValueError("Обнаружен матч без match_id.")

        match_ids.append(match_id)

        if not match.get("starting_at"):
            raise ValueError(
                f"Матч {match_id} не содержит starting_at."
            )

        if match.get("season_id") != EXPECTED_SEASON_ID:
            raise ValueError(
                f"Матч {match_id} относится не к сезону "
                f"{EXPECTED_SEASON_ID}."
            )

    if len(match_ids) != len(set(match_ids)):
        raise ValueError("Обнаружены дубликаты match_id.")


def validate_teams(teams: dict[int, dict]) -> None:
    """Проверяет извлечённые данные команд."""

    if len(teams) != EXPECTED_TEAMS:
        raise ValueError(
            f"Ожидалось {EXPECTED_TEAMS} команд, "
            f"получено {len(teams)}."
        )

    for team_id, team in teams.items():
        if not team["name"]:
            raise ValueError(
                f"У команды {team_id} отсутствует name."
            )


def validate_players(player_ids: set[int]) -> None:
    """Проверяет количество уникальных игроков."""

    if len(player_ids) != EXPECTED_PLAYERS:
        raise ValueError(
            f"Ожидалось {EXPECTED_PLAYERS} игроков, "
            f"получено {len(player_ids)}."
        )


def print_summary(
    matches: list[dict],
    teams: dict[int, dict],
    player_ids: set[int],
) -> None:
    """Выводит итог проверки данных."""

    print()
    print("Проверка завершена успешно.")
    print()
    print(f"Матчей:       {len(matches)}")
    print(f"Команд:       {len(teams)}")
    print(f"Игроков:      {len(player_ids)}")
    print()


def main() -> None:
    print("Загружаем сезон 2025/26...")

    matches = load_json(SEASON_PATH)

    print(f"Загружено матчей: {len(matches)}")

    print("Извлекаем команды...")
    teams = extract_teams(matches)

    print("Извлекаем игроков...")
    player_ids = extract_players(matches)

    print("Проверяем данные...")

    validate_matches(matches)
    validate_teams(teams)
    validate_players(player_ids)

    print_summary(matches, teams, player_ids)


if __name__ == "__main__":
    main()
