import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / 'config' / 'secrets.env'
load_dotenv(env_path)

class WeatherConfig:
    API_KEY = os.getenv('OPENWEATHER_API_KEY')
    BASE_URL = 'http://api.openweathermap.org/data/2.5'

    CITIES = ['Minsk']

    UNITS = 'metric'
    LANGUAGE = 'ru'

    OUTPUT_PATH = '/tmp/weather_data'


# class DatabaseConfig:
    """Конфигурация для базы данных (если понадобится)"""

    # DB_HOST = os.getenv('DB_HOST', 'localhost')
    # DB_PORT = os.getenv('DB_PORT', '5432')
    # DB_NAME = os.getenv('DB_NAME', 'weather_db')
    # DB_USER = os.getenv('DB_USER')
    # DB_PASSWORD = os.getenv('DB_PASSWORD')



