import os
import urllib.request
import duckdb

# ==========================================
# 1. SETUP & CONFIGURATION (Menggunakan Raw & Processed)
# ==========================================
months = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/"

# Menggunakan penamaan folder kamu sendiri
raw_path = r"C:\KULIAH\S6\RDV\project\data\raw"
output_path = r"C:\KULIAH\S6\RDV\project\data\processed"

os.makedirs(raw_path, exist_ok=True)
os.makedirs(output_path, exist_ok=True)

print(f"Raw (Mentah) path ready: {raw_path}")
print(f"Processed (Matang) path ready: {output_path}")

# ==========================================
# 2. INGESTION (Download File ke Bronze)
# ==========================================
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

# ==========================================
# 3. TRANSFORMATION & SAVING (Menggunakan DuckDB)
# ==========================================
print("\n--- Starting Data Processing via DuckDB ---")

# Inisialisasi koneksi in-memory DuckDB
con = duckdb.connect()

# Path pola untuk membaca seluruh file parquet sekaligus
# DuckDB mendukung wildcard (*) untuk membaca multi-file sekaligus!
parquet_pattern = os.path.join(raw_path, "yellow_tripdata_2025-*.parquet")

# Definisikan query untuk seleksi kolom dan menambahkan metadata bulan
# Kita mengambil nama file (filename) untuk diekstrak menjadi kolom 'month'
query = """
    SELECT 
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        PULocationID,
        DOLocationID,
        trip_distance,
        fare_amount,
        -- Mengambil string tahun-bulan dari nama file (misal: '2025-01')
        regexp_extract(filename, 'yellow_tripdata_(\d{4}-\d{2})\.parquet', 1) AS month
    FROM read_parquet(?, filename=true)
"""

print("Processing and combining data using DuckDB...")
# Eksekusi query dan langsung simpan ke Silver layer dengan teknik Hive Partitioning
# Data akan otomatis terbagi menjadi folder-folder kecil berdasarkan 'month'
output_parquet_path = os.path.join(output_path, "taxi_processed")

con.execute(f"""
    COPY ({query}) 
    TO '{output_parquet_path}' 
    (FORMAT PARQUET, PARTITION_BY month, OVERWRITE_OR_IGNORE 1);
""", [parquet_pattern])

print(f"Data successfully processed and saved to Hive Partition at: {output_parquet_path}")

# ==========================================
# 4. VERIFIKASI DATA (Opsional)
# ==========================================
print("\n--- Verifying Processed Data ---")
# Cek info total baris menggunakan DuckDB (Sangat cepat!)
total_rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{output_parquet_path}/**/*.parquet')").fetchone()[0]
print(f"Total rows in combined dataset: {total_rows:,}")

# Intip 5 data teratas menggunakan Pandas (hanya untuk display head)
preview_df = con.execute(f"SELECT * FROM read_parquet('{output_parquet_path}/**/*.parquet') LIMIT 5").df()
print("\nPreview Data:")
print(preview_df)