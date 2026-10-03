import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("SPORTMONKS_API_TOKEN")
SEASON_ID = 25598

OUTPUT_DIR = Path("data/raw/season_stats")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FIXTURES_URL = "https://api.sportmonks.com/v3/football/fixtures"


# Получаем список всех матчей выбранного сезона.
params = {
    "api_token": TOKEN,
    "filters": f"fixtureSeasons:{SEASON_ID}",
    "per_page": 25,
}

all_fixtures = []
page = 1

while True:
    params["page"] = page

    response = requests.get(FIXTURES_URL, params=params)
    response.raise_for_status()

    data = response.json()
    all_fixtures.extend(data["data"])

    if not data["pagination"]["has_more"]:
        break

    page += 1

print(f"Всего матчей: {len(all_fixtures)}")


# Получаем подробную статистику каждого матча.
results = []
failed = []

for i, fixture in enumerate(all_fixtures, start=1):
    fixture_id = fixture["id"]

    print(f"[{i}/{len(all_fixtures)}] fixture {fixture_id}")

    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"

    params = {
        "api_token": TOKEN,
        "include": "participants;lineups.details.type;statistics.type",
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"  Ошибка HTTP {response.status_code}")

        failed.append(
            {
                "fixture_id": fixture_id,
                "status_code": response.status_code,
            }
        )
        continue

    fixture_data = response.json()["data"]
    results.append(fixture_data)


# Сохраняем данные всего сезона.
output_path = OUTPUT_DIR / "season_2025_26.json"

with open(output_path, "w", encoding="utf-8") as file:
    json.dump(
        results,
        file,
        ensure_ascii=False,
        indent=2,
    )


# Сохраняем информацию о неудачных запросах.
failed_path = OUTPUT_DIR / "failed.json"

with open(failed_path, "w", encoding="utf-8") as file:
    json.dump(
        failed,
        file,
        ensure_ascii=False,
        indent=2,
    )


print()
print("=" * 60)
print("Загрузка сезона завершена")
print("=" * 60)
print(f"Успешно: {len(results)}")
print(f"Ошибок: {len(failed)}")
print()
print(f"Данные: {output_path}")
print(f"Ошибки: {failed_path}")