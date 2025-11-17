# Airflow Weather Data Collector
![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

## Описание
Проект для сбора данных о погоде в Минске с использованием Apache Airflow.

## Функциональность
- Ежечасный сбор данных о температуре и ветре
- Сохранение в Parquet файлы
- Интеграция с OpenWeatherMap API

## Установка
1. Склонируйте репозиторий
2. Создайте файл `.env` с переменными окружения
3. Запустите:
   ```bash
   docker-compose up -d
   ```
