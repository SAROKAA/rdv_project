import os
import urllib.request
import duckdb

months = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/"

raw_path = r"C:\KULIAH\S6\RDV\project\data\raw"
output_path = r"C:\KULIAH\S6\RDV\project\data\processed"

os.makedirs(raw_path, exist_ok=True)
os.makedirs(output_path, exist_ok=True)

print(f"Raw (Mentah) path ready: {raw_path}")
print(f"Processed (Matang) path ready: {output_path}")

print("\n--- Starting Data Ingestion ---")
for month in months:
    file_name = f"yellow_tripdata_{month}.parquet"
    url = base_url + file_name
    save_path = os.path.join(raw_path, file_name)

    if not os.path.exists(save_path):
        print(f"Downloading {file_name}...")
        try:
            urllib.request.urlretrieve(url, save_path)
            print(f"Saved: {save_path}")
        except Exception as e:
            print(f"Failed to download {file_name}: {e}")
    else:
        print(f"{file_name} already exists in Bronze layer.")

print("\n--- Starting Data Processing via DuckDB ---")

con = duckdb.connect()

parquet_pattern = os.path.join(raw_path, "yellow_tripdata_2025-*.parquet")

query = """
    SELECT 
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        PULocationID,
        DOLocationID,
        trip_distance,
        fare_amount,
        -- Mengambil string tahun-bulan dari nama file (misal: '2025-01')
        regexp_extract(filename, 'yellow_tripdata_(\d{4}-\d{2})\\.parquet', 1) AS month
    FROM read_parquet(?, filename=true)
"""

print("Processing and combining data using DuckDB...")
output_parquet_path = os.path.join(output_path, "taxi_processed")

con.execute(f"""
    COPY ({query}) 
    TO '{output_parquet_path}' 
    (FORMAT PARQUET, PARTITION_BY month, OVERWRITE_OR_IGNORE 1);
""", [parquet_pattern])

print(f"Data successfully processed and saved to Hive Partition at: {output_parquet_path}")

print("\n--- Verifying Processed Data ---")
total_rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{output_parquet_path}/**/*.parquet')").fetchone()[0]
print(f"Total rows in combined dataset: {total_rows:,}")

preview_df = con.execute(f"SELECT * FROM read_parquet('{output_parquet_path}/**/*.parquet') LIMIT 5").df()
print("\nPreview Data:")
print(preview_df)