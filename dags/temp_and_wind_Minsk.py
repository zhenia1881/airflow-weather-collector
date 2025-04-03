# dags/temp_and_wind.py
import os
import pandas as pd
from datetime import timedelta
from airflow.decorators import dag, task

from helpers.weather_api import WeatherAPI

CITY = "Minsk"
DATE_FMT = "%Y_%m_%d"
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"
OUTPUT_DIR = "/opt/airflow/data"  # проброси volume ./data -> /opt/airflow/data


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def append_parquet_safe(new_df: pd.DataFrame, path: str):
    if os.path.exists(path):
        try:
            existing = pd.read_parquet(path)
            merged = pd.concat([existing, new_df], ignore_index=True)
            merged = merged.drop_duplicates(subset=["datetime"]).sort_values("datetime")
            merged.to_parquet(path, index=False)
        except Exception as e:
            print(f"Warning: failed to read existing parquet {path}: {e}. Overwriting.")
            new_df.to_parquet(path, index=False)
    else:
        new_df.to_parquet(path, index=False)


@dag(
    dag_id="minsk_temp_and_wind_hourly",
    description="Ежечасная сборка температуры и ветра для Минска с сохранением в parquet",
    schedule="0 * * * *",           # каждый час в начале часа
    start_date=None,                 # в Airflow 3 можно не указывать; управление началом — через включение DAG
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["weather", "minsk", "parquet"],
)
def minsk_temp_and_wind_hourly():
    @task
    def fetch_transform_save(**context):
        """
        Используем logical_date из контекста для стабильной почасовой отметки.
        Airflow 3 автоматически передаёт контекст, если задача принимает **kwargs.
        """
        ensure_output_dir()

        api = WeatherAPI()
        raw = api.get_weather_by_city(CITY)

        # Берём логическое время начала интервала выполнения (UTC) и пишем его как локальное время Минска, если нужно.
        # Если хочешь именно локальную метку Europe/Minsk, раскомментируй блок ниже.
        logical_dt = context["logical_date"]  # pendulum DateTime (UTC)
        # from pendulum import timezone
        # minsk_tz = timezone("Europe/Minsk")
        # now = logical_dt.in_timezone(minsk_tz).naive()
        # dt_str = now.strftime(DATETIME_FMT)
        # day_str = now.strftime(DATE_FMT)

        # По умолчанию используем UTC logical_date для детерминированности,
        # чтобы каждый ран давал ровно одну строку.
        dt_str = logical_dt.strftime(DATETIME_FMT)
        day_str = logical_dt.strftime(DATE_FMT)

        temp_filename = os.path.join(OUTPUT_DIR, f"minsk_{day_str}_temp.parquet")
        wind_filename = os.path.join(OUTPUT_DIR, f"minsk_{day_str}_wind.parquet")

        # Температурный ряд
        temp_row = {
            "datetime": dt_str,
            "temp": float(raw["main"]["temp"]),
            "feels_like": float(raw["main"]["feels_like"]),
            "temp_min": float(raw["main"].get("temp_min", raw["main"]["temp"])),
            "temp_max": float(raw["main"].get("temp_max", raw["main"]["temp"])),
            "pressure": int(raw["main"]["pressure"]),
        }
        temp_df_new = pd.DataFrame([temp_row])

        # Ветер
        wind = raw.get("wind", {}) or {}
        wind_row = {
            "datetime": dt_str,
            "speed": float(wind.get("speed", 0.0)),
            "deg": float(wind.get("deg", 0.0)),
            "gust": float(wind.get("gust", 0.0)),
        }
        wind_df_new = pd.DataFrame([wind_row])

        # Дополнение parquet
        append_parquet_safe(temp_df_new, temp_filename)
        append_parquet_safe(wind_df_new, wind_filename)

    fetch_transform_save()


dag = minsk_temp_and_wind_hourly()

