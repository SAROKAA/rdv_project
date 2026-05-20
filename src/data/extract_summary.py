import duckdb
import os
import pandas as pd

# ==========================================
# 1. SETUP PATH DATABASE & OUTPUT
# ==========================================
db_path = r"C:\KULIAH\S6\RDV\project\data\processed\rdv_project.duckdb"
output_dir = r"C:\KULIAH\S6\RDV\project\data\processed\csv_export"

print(f"Menghubungkan ke DuckDB: {db_path}")
con = duckdb.connect(db_path)

# Pastikan folder output sudah ada
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Deteksi nama kolom di dim_location secara otomatis (apakah location_id atau PULocationID)
columns_info = con.execute("PRAGMA table_info('dim_location')").df()
loc_col = 'location_id' if 'location_id' in columns_info['name'].values else 'PULocationID'

print("\n--- 1. Membuat CSV Total Trip per PULocationID ---")
# Query untuk menghitung total trip per lokasi jemput
query_zone = """
    SELECT 
        PULocationID, 
        COUNT(*) AS total_trip
    FROM fact_taxi_trip
    GROUP BY PULocationID
    ORDER BY PULocationID
"""
df_zone = con.execute(query_zone).df()
zone_output_path = os.path.join(output_dir, "total_trips_per_zone.csv")
df_zone.to_csv(zone_output_path, index=False)
print(f"-> Sukses! File format zone disimpan di: {zone_output_path}")


print("\n--- 2. Membuat CSV Total Trip per Borough ---")
# Query untuk menghitung total trip per wilayah (Borough) dengan melakukan JOIN ke dim_location
query_borough = f"""
    SELECT 
        l.borough, 
        COUNT(*) AS total_trip
    FROM fact_taxi_trip t
    JOIN dim_location l ON t.PULocationID = l.{loc_col}
    GROUP BY l.borough
    ORDER BY total_trip DESC
"""
df_borough = con.execute(query_borough).df()
borough_output_path = os.path.join(output_dir, "total_trips_per_borough.csv")
df_borough.to_csv(borough_output_path, index=False)
print(f"-> Sukses! File format borough disimpan di: {borough_output_path}")

con.close()
print("\n--- [SELESAI] Kedua File Ringkasan Berhasil Dibuat! ---")