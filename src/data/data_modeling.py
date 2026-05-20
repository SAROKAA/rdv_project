import os
import duckdb
import pandas as pd

# ==========================================
# 1. SETUP & CONFIGURATION (Windows Local)
# ==========================================
file_path = r"C:\KULIAH\S6\RDV\project\data\processed\taxi_weather.parquet"
db_path = r"C:\KULIAH\S6\RDV\project\data\processed\rdv_project.duckdb"

print(f"Membaca data terintegrasi dari: {file_path}")
print(f"Target file database: {db_path}")

con = duckdb.connect(db_path)
print("Berhasil terhubung ke DuckDB.")

# ==========================================
# 2. DOWNLOAD KAMUS DATA ZONA LOKASI NYC TLC
# ==========================================
print("\n--- Mengunduh Kamus Data Zona Resmi NYC TLC ---")
url_zone = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
df_zone = pd.read_csv(url_zone)

con.register("raw_zone_lookup", df_zone)
print("Kamus data lokasi berhasil di-load ke DuckDB.")

# ==========================================
# 3. PEMBUATAN TABEL DIMENSI (STAR SCHEMA)
# ==========================================
print("\n--- Membuat Tabel Dimensi (Star Schema) ---")

# A. Tabel Dimensi Waktu (dim_time) - PERBAIKAN: Menggunakan taxi_date dan generate time_category
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

# B. Tabel Dimensi Lokasi (dim_location)
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

# ==========================================
# 4. PEMBUATAN TABEL FAKTA (STAR SCHEMA)
# ==========================================
print("\n--- Membuat Tabel Fakta (Star Schema) ---")

# A. Tabel Fakta Cuaca (fact_weather) - PERBAIKAN: Menggunakan nama kolom taxi_date & taxi_hour
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

# B. Tabel Fakta Perjalanan Taksi (fact_taxi_trip) - PERBAIKAN: Generate trip_category & sesuaikan nama kolom tanggal/jam
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

# ==========================================
# 5. VERIFIKASI HASIL AKHIR
# ==========================================
print("\nDaftar Tabel di Dalam rdv_project.duckdb:")
print(con.execute("SHOW TABLES").fetchdf())

con.close()
print("\nKoneksi database ditutup. Langkah Pemodelan Selesai!")