import duckdb
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# 1. Hubungkan ke DuckDB Lokal
db_path = r"C:\KULIAH\S6\RDV\project\data\processed\rdv_project.duckdb"
con = duckdb.connect(db_path)

query = """
    SELECT 
        t.pickup_date,
        t.pickup_hour,
        t.PULocationID AS location_id,
        COUNT(*) AS total_demand, -- Target yang mau diprediksi (Y)
        AVG(w.temperature) AS temperature,
        AVG(w.precipitation) AS precipitation,
        AVG(w.weathercode) AS weathercode
    FROM fact_taxi_trip t
    LEFT JOIN fact_weather w 
        ON t.pickup_date = w.pickup_date AND t.pickup_hour = w.pickup_hour
    GROUP BY t.pickup_date, t.pickup_hour, t.PULocationID
    LIMIT 500000 -- Batasan sampling agar training cepat di laptop
"""

df_ml = con.execute(query).df()
con.close()

# 2. Feature Engineering Tambahan (Ekstrak Hari)
df_ml['pickup_date'] = pd.to_datetime(df_ml['pickup_date'])
df_ml['day_of_week'] = df_ml['pickup_date'].dt.dayofweek # 0=Senin, 6=Minggu

# 3. Tentukan Fitur (X) dan Target (Y)
X = df_ml[['pickup_hour', 'location_id', 'temperature', 'precipitation', 'weathercode', 'day_of_week']]
y = df_ml['total_demand']

# Split data menjadi Train (80%) dan Test (20%)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Data Siap! Sesi Training dengan {len(X_train)} baris data...")

# 4. Training Menggunakan XGBoost Regressor
model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42)
model.fit(X_train, y_train)

# 5. Evaluasi Model
y_pred = model.predict(X_test)
print("\n--- Hasil Evaluasi Model Forecasting ---")
print(f"Mean Absolute Error (MAE): {mean_absolute_error(y_test, y_pred):.2f} perjalanan")
print(f"R2 Score (Akurasi): {r2_score(y_test, y_pred)*100:.2f}%")