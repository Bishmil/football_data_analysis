import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


# Загружаем переменные окружения из .env
load_dotenv()


# Подключение к PostgreSQL
engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)


# Таблицы, которые используются как источник данных для Power BI
TABLES = [
    "leagues",
    "seasons",
    "teams",
    "players",
    "positions",
    "matches",
    "team_match",
    "player_match",
]


# Папка для BI-выгрузок
OUTPUT_DIR = Path("data/bi")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print("Подключение создано")
print(f"Папка выгрузки: {OUTPUT_DIR.resolve()}")
print()


# Выгрузка таблиц
for table in TABLES:
    query = f"SELECT * FROM {table}"

    df = pd.read_sql(query, engine)

    output_path = OUTPUT_DIR / f"{table}.csv"
    df.to_csv(output_path, index=False)

    print(
        f"{table:<15} "
        f"rows: {len(df):>5} | "
        f"columns: {len(df.columns):>2} | "
        f"file: {output_path}"
    )


print()
print("Выгрузка завершена.")