import duckdb
import os

db_path = r"C:\KULIAH\S6\RDV\project\data\processed\rdv_project.duckdb"
output_dir = r"C:\KULIAH\S6\RDV\project\data\processed\csv_export"

print(f"Membuka database dari: {db_path}")

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Membuat folder output baru di: {output_dir}")

con = duckdb.connect(db_path)

tables = ['dim_time', 'dim_location', 'fact_weather', 'fact_taxi_trip']

print("\n--- Memulai Proses Ekspor ke CSV ---")

for table in tables:
    output_file = os.path.join(output_dir, f"{table}.csv")
    print(f"Mengekspor tabel '{table}'...")
    con.execute(f"COPY {table} TO '{output_file}' (HEADER, DELIMITER ',');")
    print(f"-> Sukses! File tersimpan di: {output_file}")

con.close()
print("\n--- [SELESAI] Semua Tabel Berhasil Dikonversi ke CSV! ---")
print(f"Silakan buka folder ini untuk mengambil file kelompokmu:\n{output_dir}")