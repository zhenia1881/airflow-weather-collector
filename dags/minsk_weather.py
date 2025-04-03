from datetime import datetime, timedelta
import requests
import pandas as pd
import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
import logging

# Координаты Минска
MINSK_LAT = 53.9045
MINSK_LON = 27.5615

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'provide_context': True,
}


def get_weather_data(**kwargs):
    """Получение данных о погоде через API OpenWeatherMap"""
    try:
        conn = BaseHook.get_connection('openweathermap')
        api_key = conn.password

        params = {
            'lat': MINSK_LAT,
            'lon': MINSK_LON,
            'appid': api_key,
            'units': 'metric'
        }

        response = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params=params,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        logging.info(f"Successfully fetched weather data: {data}")
        return data

    except Exception as e:
        logging.error(f"Error fetching weather data: {str(e)}")
        raise


def process_temp_data(**kwargs):
    """Обработка и сохранение данных о температуре"""
    ti = kwargs['ti']
    try:
        data = ti.xcom_pull(task_ids='get_weather_data')

        if not data or 'main' not in data:
            raise ValueError("Invalid weather data structure")

        main_data = data['main']
        dt = datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S')

        temp_df = pd.DataFrame([{
            'datetime': dt,
            'temp': main_data.get('temp'),
            'feels_like': main_data.get('feels_like'),
            'temp_min': main_data.get('temp_min'),
            'temp_max': main_data.get('temp_max'),
            'pressure': main_data.get('pressure'),
            'humidity': main_data.get('humidity'),
        }])

        date_str = datetime.now().strftime('%Y_%m_%d')
        os.makedirs('/opt/airflow/data', exist_ok=True)
        file_path = f'/opt/airflow/data/minsk_{date_str}_temp.parquet'

        if os.path.exists(file_path):
            existing_df = pd.read_parquet(file_path)
            updated_df = pd.concat([existing_df, temp_df], ignore_index=True)
            updated_df.to_parquet(file_path, index=False)
        else:
            temp_df.to_parquet(file_path, index=False)

        logging.info(f"Successfully saved temperature data to {file_path}")

    except Exception as e:
        logging.error(f"Error processing temperature data: {str(e)}")
        raise


def process_wind_data(**kwargs):
    """Обработка и сохранение данных о ветре"""
    ti = kwargs['ti']
    try:
        data = ti.xcom_pull(task_ids='get_weather_data')

        if not data or 'wind' not in data:
            raise ValueError("Invalid weather data structure")

        wind_data = data['wind']
        dt = datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S')

        wind_df = pd.DataFrame([{
            'datetime': dt,
            'speed': wind_data.get('speed'),
            'deg': wind_data.get('deg'),
            'gust': wind_data.get('gust'),
        }])

        date_str = datetime.now().strftime('%Y_%m_%d')
        os.makedirs('/opt/airflow/data', exist_ok=True)
        file_path = f'/opt/airflow/data/minsk_{date_str}_wind.parquet'

        if os.path.exists(file_path):
            existing_df = pd.read_parquet(file_path)
            updated_df = pd.concat([existing_df, wind_df], ignore_index=True)
            updated_df.to_parquet(file_path, index=False)
        else:
            wind_df.to_parquet(file_path, index=False)

        logging.info(f"Successfully saved wind data to {file_path}")

    except Exception as e:
        logging.error(f"Error processing wind data: {str(e)}")
        raise


with DAG(
        'minsk_weather_collection',
        default_args=default_args,
        description='Collect hourly weather data for Minsk using coordinates',
        schedule_interval='@hourly',
        catchup=False,
        max_active_runs=1,
        tags=['weather', 'minsk'],
) as dag:
    get_weather_task = PythonOperator(
        task_id='get_weather_data',
        python_callable=get_weather_data,
    )

    process_temp_task = PythonOperator(
        task_id='process_temp_data',
        python_callable=process_temp_data,
    )

    process_wind_task = PythonOperator(
        task_id='process_wind_data',
        python_callable=process_wind_data,
    )

    get_weather_task >> [process_temp_task, process_wind_task]