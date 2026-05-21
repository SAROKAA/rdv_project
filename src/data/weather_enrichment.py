import os
import requests
import pandas as pd
import duckdb

input_taxi_path = r"C:\KULIAH\S6\RDV\project\data\processed\taxi_cleaned.parquet"
output_final_path = r"C:\KULIAH\S6\RDV\project\data\processed\taxi_weather.parquet"

print(f"Reading cleaned taxi data from: {input_taxi_path}")
print(f"Target enriched output path: {output_final_path}")

print("\n--- Fetching HOURLY Weather Data from Open-Meteo API ---")

url = "https://archive-api.open-meteo.com/v1/archive"
weather_params = {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "start_date": "2025-01-01",
    "end_date": "2025-06-30",
    "hourly": "temperature_2m,precipitation,weathercode",
    "timezone": "America/New_York"
}

try:
    response = requests.get(url, params=weather_params)
    response.raise_for_status()
    weather_json = response.json()
    
    hourly_data = weather_json['hourly']
    weather_df = pd.DataFrame({
        "datetime": pd.to_datetime(hourly_data['time']),
        "temperature_2m": hourly_data['temperature_2m'],
        "precipitation": hourly_data['precipitation'],
        "weathercode": hourly_data['weathercode']
    })
    
    weather_df['weather_date'] = weather_df['datetime'].dt.strftime('%Y-%m-%d')
    weather_df['weather_hour'] = weather_df['datetime'].dt.hour
    
    print(f"Weather data successfully downloaded. Total hourly rows: {len(weather_df)}")
    
except Exception as e:
    print(f"Error fetching weather data: {e}")
    exit()

print("\n--- Merging Taxi Data with Hourly Weather Data via DuckDB ---")

con = duckdb.connect()

con.register("weather_table", weather_df)

enrichment_query = f"""
    WITH taxi_prepared AS (
        SELECT 
            *,
            -- Mengonversi pickup datetime menjadi string tanggal (YYYY-MM-DD)
            strftime(tpep_pickup_datetime, '%Y-%m-%d') AS taxi_date,
            -- Mengambil komponen jam (0-23) untuk pencocokan hourly cuaca
            EXTRACT(HOUR FROM tpep_pickup_datetime) AS taxi_hour
        FROM read_parquet('{input_taxi_path}')
    )
    SELECT 
        t.*,
        w.temperature_2m,
        w.precipitation,
        w.weathercode
    FROM taxi_prepared t
    LEFT JOIN weather_table w 
        ON t.taxi_date = w.weather_date 
        AND t.taxi_hour = w.weather_hour
"""

print("Executing merge query and streaming directly to final Parquet...")
con.execute(f"""
    COPY ({enrichment_query}) 
    TO '{output_final_path}' 
    (FORMAT PARQUET, OVERWRITE_OR_IGNORE 1);
""")

print(f"Enriched data successfully saved to: {output_final_path}")

print("\n--- Verifying Enriched Data ---")

total_rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{output_final_path}')").fetchone()[0]
print(f"Total rows in final dataset: {total_rows:,}")

print("\nPreview Sample Data (5 baris dengan kolom cuaca baru):")
preview_df = con.execute(f"""
    SELECT 
        taxi_date,
        taxi_hour,
        trip_distance, 
        fare_amount, 
        temperature_2m, 
        precipitation,
        weathercode
    FROM read_parquet('{output_final_path}') 
    LIMIT 5
""").df()
print(preview_df)

con.close()