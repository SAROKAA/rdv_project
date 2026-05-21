import os
import duckdb
import pandas as pd

file_path = r"C:\KULIAH\S6\RDV\project\data\processed\taxi_weather.parquet"
db_path = r"C:\KULIAH\S6\RDV\project\data\processed\rdv_project.duckdb"

print(f"Membaca data terintegrasi dari: {file_path}")
print(f"Target file database: {db_path}")

con = duckdb.connect(db_path)
print("Berhasil terhubung ke DuckDB.")

print("\n--- Mengunduh Kamus Data Zona Resmi NYC TLC ---")
url_zone = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
df_zone = pd.read_csv(url_zone)

con.register("raw_zone_lookup", df_zone)
print("Kamus data lokasi berhasil di-load ke DuckDB.")

print("\n--- Membuat Tabel Dimensi (Star Schema) ---")

print("Membuat tabel dim_time...")
con.execute(f"""
    CREATE OR REPLACE TABLE dim_time AS
    SELECT 
        ROW_NUMBER() OVER () AS time_id,
        taxi_date AS pickup_date,
        taxi_hour AS pickup_hour,
        CASE 
            WHEN taxi_hour >= 5 AND taxi_hour < 12 THEN 'Pagi'
            WHEN taxi_hour >= 12 AND taxi_hour < 18 THEN 'Siang'
            ELSE 'Malam'
        END AS time_category
    FROM (
        SELECT DISTINCT 
            taxi_date, 
            taxi_hour
        FROM read_parquet('{file_path}')
    );
""")

print("Membuat tabel dim_location...")
con.execute("""
    CREATE OR REPLACE TABLE dim_location AS
    SELECT 
        LocationID AS location_id,
        Borough AS borough,
        Zone AS zone_name,
        service_zone
    FROM raw_zone_lookup;
""")

print("\n--- Membuat Tabel Fakta (Star Schema) ---")

print("Membuat tabel fact_weather...")
con.execute(f"""
    CREATE OR REPLACE TABLE fact_weather AS
    SELECT DISTINCT 
        taxi_date AS pickup_date,
        taxi_hour AS pickup_hour,
        temperature_2m AS temperature,
        precipitation,
        weathercode
    FROM read_parquet('{file_path}');
""")

print("Membuat tabel fact_taxi_trip...")
con.execute(f"""
    CREATE OR REPLACE TABLE fact_taxi_trip AS
    SELECT 
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        taxi_date AS pickup_date,
        taxi_hour AS pickup_hour,
        PULocationID,
        DOLocationID,
        trip_distance,
        fare_amount,
        trip_duration,
        CASE 
            WHEN trip_distance < 3.0 THEN 'Pendek'
            WHEN trip_distance < 10.0 THEN 'Sedang'
            ELSE 'Jauh'
        END AS trip_category
    FROM read_parquet('{file_path}');
""")

print("\n--- Seluruh Tabel Star Schema Berhasil Diperbarui di Database! ---")

print("\nDaftar Tabel di Dalam rdv_project.duckdb:")
print(con.execute("SHOW TABLES").fetchdf())

con.close()
print("\nKoneksi database ditutup. Langkah Pemodelan Selesai!")