import pandas as pd

# Для файла с температурой
temp_df = pd.read_parquet('data/minsk_2025_04_03_temp.parquet')
print("Temperature Data:")
print(temp_df.head())

# Для файла с ветром
wind_df = pd.read_parquet('data/minsk_2025_04_03_wind.parquet')
print("\nWind Data:")
print(wind_df.head())