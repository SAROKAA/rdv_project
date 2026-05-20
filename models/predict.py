import pickle
import os
import pandas as pd

class TaxiDemandPredictor:
    def __init__(self, model_path=None):
        """
        Inisialisasi class dan langsung load file model .pkl
        """
        if model_path is None:
            # Set default path ke folder models projectmu
            self.model_path = r"C:\KULIAH\S6\RDV\project\models\model_demand.pkl"
        else:
            self.model_path = model_path
            
        self.model = self._load_model()
        # Susunan fitur harus persis sama dengan saat training!
        self.feature_columns = ['pickup_hour', 'location_id', 'temperature', 'precipitation', 'weathercode', 'day_of_week']

    def _load_model(self):
        """
        Fungsi internal untuk me-load model binary pickle
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Aduh, file model tidak ditemukan di: {self.model_path}. Sudah jalanin train.py belum?")
        
        print(f" Mengambil model dari {self.model_path}...")
        with open(self.model_path, "rb") as f:
            return pickle.load(f)

    def predict(self, input_data):
        """
        Fungsi utama untuk memprediksi demand taksi.
        Bisa menerima input berupa Dictionary (single data) atau Pandas DataFrame (batch data).
        """
        # Jika input berupa dictionary tunggal, ubah ke DataFrame dulu
        if isinstance(input_data, dict):
            df_input = pd.DataFrame([input_data])
        elif isinstance(input_data, pd.DataFrame):
            df_input = input_data.copy()
        else:
            raise ValueError("Format input salah! Gunakan Dictionary atau Pandas DataFrame.")

        # Pastikan kolom day_of_week otomatis terisi jika ada input tanggal
        if 'pickup_date' in df_input.columns and 'day_of_week' not in df_input.columns:
            df_input['pickup_date'] = pd.to_datetime(df_input['pickup_date'])
            df_input['day_of_week'] = df_input['pickup_date'].dt.dayofweek

        # Validasi apakah semua fitur yang dibutuhkan sudah lengkap
        missing_features = [col for col in self.feature_columns if col not in df_input.columns]
        if missing_features:
            raise KeyError(f"Input data kurang fitur penting ini: {missing_features}")

        # Urutkan posisi kolom sesuai dengan kebutuhan model XGBoost saat training
        X = df_input[self.feature_columns]
        
        # Eksekusi prediksi matematika XGBoost
        predictions = self.model.predict(X)
        
        return predictions

# ==========================================
# CONTOH CARA PENGGUNAAN LANGSUNG (SIMULASI)
# ==========================================
if __name__ == "__main__":
    print("--- Simulasi Pemanggilan Class Predictor ---")
    
    # 1. Instansiasi Class
    predictor = TaxiDemandPredictor()
    
    # 2. Siapkan data simulasi (misal: Jam 5 sore, di Manhattan (ID: 142), suhu 22C, mendung gerimis)
    data_baru = {
        'pickup_hour': 17,
        'location_id': 142,
        'temperature': 22.5,
        'precipitation': 0.8,
        'weathercode': 51,
        'day_of_week': 4   
    }
    
    # 3. Panggil fungsi predict
    hasil_prediksi = predictor.predict(data_baru)
    
    print("\n[HASIL PREDIKSI]")
    print(f"Prediksi jumlah permintaan taksi pada kondisi tersebut: {int(hasil_prediksi[0])} orderan per jam.")