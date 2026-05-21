import duckdb
import pandas as pd
import pickle
import os
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score

db_path = r"C:\KULIAH\S6\RDV\project\data\processed\rdv_project.duckdb"
con = duckdb.connect(db_path)

print("--- Menarik Data Agregat untuk Training Model ---")
query = """
    SELECT 
        t.pickup_date,
        t.pickup_hour,
        t.PULocationID AS location_id,
        COUNT(*) AS total_demand, 
        AVG(w.temperature) AS temperature,
        AVG(w.precipitation) AS precipitation,
        AVG(w.weathercode) AS weathercode
    FROM fact_taxi_trip t
    LEFT JOIN fact_weather w 
        ON t.pickup_date = w.pickup_date AND t.pickup_hour = w.pickup_hour
    WHERE EXTRACT(MONTH FROM t.tpep_pickup_datetime) IN (1, 2, 3)
    GROUP BY t.pickup_date, t.pickup_hour, t.PULocationID
"""

df_ml = con.execute(query).df()
print(f"Total baris agregat data: {len(df_ml):,}")

df_ml['pickup_date'] = pd.to_datetime(df_ml['pickup_date'])
df_ml['day_of_week'] = df_ml['pickup_date'].dt.dayofweek

features = ['pickup_hour', 'location_id', 'temperature', 'precipitation', 'weathercode', 'day_of_week']
X = df_ml[features]
y = df_ml['total_demand']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Memulai proses training XGBoost...")
model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, tree_method='hist', random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

mae_value = mean_absolute_error(y_test, y_pred)
r2_value = r2_score(y_test, y_pred) * 100

print("\n=== HASIL EVALUASI MODEL ===")
print(f"Akurasi Model (R2 Score)  : {r2_value:.2f}%")
print(f"Rata-rata Error (MAE)      : {mae_value:.2f}")
print("=============================\n")

model_dir = r"C:\KULIAH\S6\RDV\project\models"
if not os.path.exists(model_dir):
    os.makedirs(model_dir)

model_path = os.path.join(model_dir, "model_demand.pkl")
with open(model_path, "wb") as f:
    pickle.dump(model, f)

print(f"-> Sukses! Model disimpan di: {model_path}")

print("\n--- Membuat Data Hasil Prediksi untuk Power BI ---")
df_ml['predicted_demand'] = model.predict(X)

df_powerbi = df_ml[['pickup_date', 'pickup_hour', 'location_id', 'total_demand', 'predicted_demand']]
df_powerbi['pickup_date'] = df_powerbi['pickup_date'].dt.strftime('%Y-%m-%d')

csv_output_path = r"C:\KULIAH\S6\RDV\project\data\processed\csv_export\fact_predicted_demand.csv"
df_powerbi.to_csv(csv_output_path, sep=';', decimal=',', index=False)

print(f"-> Sukses! File visualisasi format Indonesia disimpan di: {csv_output_path}")

con.close()