import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


# Пути к данным проекта

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PART_1_PATH = PROJECT_ROOT / "data" / "raw" / "season_stats" / "part_1.json"
PART_2_PATH = PROJECT_ROOT / "data" / "raw" / "season_stats" / "part_2.json"

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "season_stats"
OUTPUT_PATH = OUTPUT_DIR / "player_profiles.json"


# Настройки API

load_dotenv(PROJECT_ROOT / ".env")

TOKEN = os.getenv("SPORTMONKS_API_TOKEN")

if not TOKEN:
    raise ValueError("SPORTMONKS_API_TOKEN не найден в .env")

BASE_URL = "https://api.sportmonks.com/v3/football/players"


def load_json(path):
    """Загружает данные из JSON-файла."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_player_ids():
    """Собирает уникальные ID игроков из данных матчей."""

    player_ids = set()

    for path in [PART_1_PATH, PART_2_PATH]:
        print(f"Читаем {path.name}...")

        data = load_json(path)

        for fixture in data:
            for lineup in fixture.get("lineups", []):
                player_id = lineup.get("player_id")

                if player_id is not None:
                    player_ids.add(player_id)

    return sorted(player_ids)


def load_existing_profiles():
    """Загружает ранее сохранённые профили игроков."""

    if not OUTPUT_PATH.exists():
        return {}

    with open(OUTPUT_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_profiles(profiles):
    """Сохраняет профили игроков в JSON-файл."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            profiles,
            file,
            ensure_ascii=False,
            indent=2,
        )


def get_player_profile(player_id):
    """Получает профиль одного игрока из Sportmonks API."""

    url = f"{BASE_URL}/{player_id}"

    params = {
        "api_token": TOKEN,
        "include": "nationality",
    }

    response = requests.get(url, params=params, timeout=30)

    if response.status_code == 429:
        raise RuntimeError("API rate limit exceeded")

    if response.status_code != 200:
        print(
            f"Ошибка для player_id={player_id}: "
            f"{response.status_code}"
        )
        print(response.text)
        return None

    return response.json()["data"]


def main():
    print("Собираем уникальных игроков...")

    player_ids = get_player_ids()

    print(f"Всего уникальных игроков: {len(player_ids)}")

    profiles = load_existing_profiles()

    print(f"Уже загружено профилей: {len(profiles)}")

    remaining_ids = [
        player_id
        for player_id in player_ids
        if str(player_id) not in profiles
    ]

    print(f"Осталось загрузить: {len(remaining_ids)}")

    if not remaining_ids:
        print("Все профили уже загружены.")
        return

    # Загружаем профили по одному и сохраняем результат
    # после каждого успешного запроса, чтобы не потерять прогресс.

    for index, player_id in enumerate(remaining_ids, start=1):
        print(
            f"[{index}/{len(remaining_ids)}] "
            f"Получаем player_id={player_id}..."
        )

        try:
            profile = get_player_profile(player_id)

        except RuntimeError as error:
            print()
            print(f"Остановка: {error}")
            print(f"Сохранено профилей: {len(profiles)}")
            print(f"Файл: {OUTPUT_PATH}")
            return

        if profile is None:
            print("Профиль не загружен.")
            continue

        # Сохраняем только данные, необходимые для базы данных.

        profiles[str(player_id)] = {
            "player_id": profile.get("id"),
            "name": profile.get("name"),
            "date_of_birth": profile.get("date_of_birth"),
            "height": profile.get("height"),
            "weight": profile.get("weight"),
            "nationality": (
                profile.get("nationality", {}).get("name")
                if profile.get("nationality")
                else None
            ),
        }

        save_profiles(profiles)

        print("Сохранено.")

        # Небольшая пауза между запросами к API.

        time.sleep(0.2)

    print()
    print("Готово.")
    print(f"Загружено профилей: {len(profiles)}")
    print(f"Файл: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
