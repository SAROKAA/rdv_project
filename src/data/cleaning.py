import os
import duckdb

input_path = r"C:\KULIAH\S6\RDV\project\data\processed\taxi_processed"
output_path = r"C:\KULIAH\S6\RDV\project\data\processed"

local_glob_pattern = os.path.join(input_path, "**", "*.parquet")
cleaned_file_path = os.path.join(output_path, "taxi_cleaned.parquet")

print(f"Reading processed data from: {input_path}")
print(f"Cleaned data will be saved to: {cleaned_file_path}")

print("\n--- Starting Data Cleaning & Transformation ---")

con = duckdb.connect()

cleaning_query = f"""
    WITH raw_data AS (
        SELECT 
            tpep_pickup_datetime,
            tpep_dropoff_datetime,
            PULocationID,
            DOLocationID,
            trip_distance,
            fare_amount,
            month,
            -- Feature Engineering 1: Menghitung durasi perjalanan (dalam menit)
            date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) / 60.0 AS trip_duration,
            -- Feature Engineering 2: Mengambil jam pickup
            EXTRACT(HOUR FROM tpep_pickup_datetime) AS pickup_hour
        FROM read_parquet('{local_glob_pattern}')
        WHERE 
            -- Langkah Dropna: Memastikan kolom kunci tidak bernilai NULL
            tpep_pickup_datetime IS NOT NULL AND
            tpep_dropoff_datetime IS NOT NULL AND
            PULocationID IS NOT NULL AND
            DOLocationID IS NOT NULL AND
            trip_distance IS NOT NULL AND
            fare_amount IS NOT NULL
    )
    SELECT 
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        PULocationID,
        DOLocationID,
        trip_distance,
        fare_amount,
        month,
        trip_duration,
        pickup_hour,
        -- Feature Engineering 3: Kategori Waktu (Menggantikan fungsi categorize_time)
        CASE 
            WHEN pickup_hour >= 5 AND pickup_hour < 12 THEN 'Pagi'
            WHEN pickup_hour >= 12 AND pickup_hour < 18 THEN 'Siang'
            ELSE 'Malam'
        END AS time_category,
        -- Feature Engineering 4: Kategori Jarak (Menggantikan fungsi categorize_trip)
        CASE 
            WHEN trip_distance < 3.0 THEN 'Pendek'
            WHEN trip_distance < 10.0 THEN 'Sedang'
            ELSE 'Jauh'
        END AS trip_category
    FROM raw_data
    WHERE 
        -- Langkah Filtering Anomali sesuai logika kodemu
        trip_distance > 0 AND
        fare_amount > 0 AND
        trip_duration > 0 AND trip_duration <= 300 AND
        PULocationID > 0 AND
        DOLocationID > 0
"""

print("Executing cleaning query and writing directly to Parquet...")
con.execute(f"""
    COPY ({cleaning_query}) 
    TO '{cleaned_file_path}' 
    (FORMAT PARQUET, OVERWRITE_OR_IGNORE 1);
""")

print("Cleaned data saved successfully!")

print("\n--- Verifying Cleaned Data ---")

total_rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{cleaned_file_path}')").fetchone()[0]
print(f"Total rows after cleaning: {total_rows:,}")

print("\nTime Category Distribution:")
print(con.execute(f"SELECT time_category, COUNT(*) as count FROM read_parquet('{cleaned_file_path}') GROUP BY time_category").df())

print("\nPreview 5 Data Teratas (Semua Kolom):")
full_preview_df = con.execute(f"SELECT * FROM read_parquet('{cleaned_file_path}') LIMIT 5").df()
print(full_preview_df)

print("\nSummary Statistics (Describe untuk kolom numerik):")
numeric_summary_df = con.execute(f"""
    SELECT 
        trip_distance, 
        fare_amount, 
        trip_duration,
        pickup_hour
    FROM read_parquet('{cleaned_file_path}')
""").df()
print(numeric_summary_df.describe())