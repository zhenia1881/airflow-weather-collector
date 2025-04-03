import requests
import pandas as pd
import datetime
from .config import WeatherConfig
from datetime import datetime

class WeatherAPI:
    def __init__(self):
        """Класс для работы с OpenWeatherMap API"""
        self.api_key = WeatherConfig.API_KEY
        self.base_url = WeatherConfig.BASE_URL
        self.units = WeatherConfig.UNITS
        self.lang = WeatherConfig.LANGUAGE

        if not self.api_key:
            raise ValueError('API_KEY не найден!')

    def get_weather_by_city(self, city_name):
        """Получить погоду для конкретного города"""
        # Было: url = f'{self.base_url}\weather'
        # Стало:
        url = f"{self.base_url}/weather"

        params = {
            # Можно уточнить страну, чтобы исключить неоднозначность:
            # 'q': f'{city_name},BY',
            'q': city_name,
            'appid': self.api_key,
            'units': self.units,
            'lang': self.lang
        }

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при запросе погоды для {city_name}: {e}")

    def get_multiple_cities_weather(self, cities=None):
        """Получить погоду для нескольких городов"""
        if cities is None:
            cities = WeatherConfig.CITIES

        weather_data = []
        for city in cities:
            try:
                data = self.get_weather_by_city(city)
                weather_data.append(self._parse_weather_data(data))
            except Exception as e:
                print(f"Ошибка для города {city}: {e}")
                continue
        return weather_data

    def _parse_weather_data(self, raw_data, forecast_data=None):
        """Парсинг данных с min/max температурами"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        today = datetime.now().strftime('%Y-%m-%d')

        # Получаем min/max за сегодня из прогноза или используем текущую как приближение
        if forecast_data and today in forecast_data:
            temp_min = forecast_data[today]['min']
            temp_max = forecast_data[today]['max']
        else:
            # Если прогноза нет, используем текущую температуру как min/max
            current_temp = raw_data['main']['temp']
            temp_min = current_temp
            temp_max = current_temp

        temp_data = {
            'city': raw_data.get('name'),
            'timestamp': timestamp,
            'date': today,
            'temperature': float(raw_data['main']['temp']),
            'feels_like': float(raw_data['main']['feels_like']),
            'temp_min': float(temp_min),
            'temp_max': float(temp_max),
            'pressure': int(raw_data['main']['pressure']),
            'humidity': int(raw_data['main'].get('humidity', 0)),
        }

        wind_data = {
            'city': raw_data.get('name'),
            'timestamp': timestamp,
            'wind_speed': float(raw_data['wind'].get('speed', 0)),
            'wind_degree': float(raw_data['wind'].get('deg', 0)) if raw_data['wind'].get('deg') else 0.0,
        }

        return [temp_data, wind_data]

def save_weather_to_parquet(weather_data, filename_temp=None, filename_wind=None):
    """Сохранить данные о погоде в Parquet"""

    if filename_temp is None:
        filename_temp = f"minsk_{datetime.now().strftime('%Y%m%d')}_temp.parquet"
    if filename_wind is None:
        filename_wind = f"minsk_{datetime.now().strftime('%Y%m%d')}_wind.parquet"

    all_temp_data = []
    all_wind_data = []

    for city_data in weather_data:
        all_temp_data.append(city_data[0])
        all_wind_data.append(city_data[1])

    try:
        pd.DataFrame(all_temp_data).to_parquet(filename_temp, index=False)
        pd.DataFrame(all_wind_data).to_parquet(filename_wind, index=False)

        print(f"Данные сохранены: {filename_temp}, {filename_wind}")
        return filename_temp, filename_wind
    except ImportError:
        print("Для работы с Parquet установите pandas и pyarrow")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")










