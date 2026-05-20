import duckdb
import os

# ==========================================
# 1. SETUP ALAMAT DATABASE & FOLDER OUTPUT
# ==========================================
db_path = r"C:\KULIAH\S6\RDV\project\data\processed\rdv_project.duckdb"
output_dir = r"C:\KULIAH\S6\RDV\project\data\processed\csv_export"

print(f"Membuka database dari: {db_path}")

# Membuat folder tujuan secara otomatis jika belum ada
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Membuat folder output baru di: {output_dir}")

# Hubungkan ke database fisik DuckDB lokal
con = duckdb.connect(db_path)

# Daftar tabel Star Schema yang akan diekspor
tables = ['dim_time', 'dim_location', 'fact_weather', 'fact_taxi_trip']

print("\n--- Memulai Proses Ekspor ke CSV ---")

# ==========================================
# 2. EKSPOR DENGAN ENGINES BAWAAN DUCKDB (SUPER CEPAT)
# ==========================================
for table in tables:
    output_file = os.path.join(output_dir, f"{table}.csv")
    print(f"Mengekspor tabel '{table}'...")
    
    # Perintah COPY TO dari DuckDB langsung menulis ke harddisk tanpa memakan RAM besar
    con.execute(f"COPY {table} TO '{output_file}' (HEADER, DELIMITER ',');")
    print(f"-> Sukses! File tersimpan di: {output_file}")

con.close()
print("\n--- [SELESAI] Semua Tabel Berhasil Dikonversi ke CSV! ---")
print(f"Silakan buka folder ini untuk mengambil file kelompokmu:\n{output_dir}")