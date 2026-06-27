import mlflow
import pandas as pd
from xgboost import XGBClassifier  # 1. Ubah import ke XGBoost
import numpy as np

mlflow.set_tracking_uri("http://127.0.0.1:5000/")

# Create a new MLflow Experiment
mlflow.set_experiment("Modelling_SML_Heart_Disesase")

target_col = 'num'

df_train = pd.read_csv("heart_disease_train.csv")

X_train = df_train.drop(columns=[target_col])
# 2. XGBoost mewajibkan label target berupa integer (dimulai dari 0)
y_train = df_train[target_col].astype(int) 

df_test = pd.read_csv("heart_disease_test.csv")

X_test = df_test.drop(columns=[target_col])
y_test = df_test[target_col].astype(int)

input_example = X_train[0:5]

with mlflow.start_run(run_name="XGBoost_Best_Model"):
    
    # 3. Definisikan parameter terbaik dari gambar
    best_params = {
        "learning_rate": 0.01,
        "max_depth": 3,
        "n_estimators": 200,
        "subsample": 0.8
    }
    
    # Log semua parameter ke MLflow sekaligus
    mlflow.log_params(best_params)
    
    # Log metadata tuning (opsional, tapi disarankan agar data MLflow Anda lengkap seperti di gambar)
    mlflow.log_param("cv_folds", 5)
    mlflow.log_param("tuning_time_s", 74.98)
    mlflow.log_param("scoring_metric", "roc_auc_ovr_weighted")
        
    mlflow.autolog()
    
    # 4. Inisialisasi model XGBoost dengan best_params
    # Menambahkan random_state agar hasilnya bisa direproduksi
    model = XGBClassifier(**best_params, random_state=42)

    # Train model
    model.fit(X_train, y_train)

    # 5. Log Model menggunakan modul xgboost bawaan MLflow
    mlflow.xgboost.log_model(
        xgb_model=model,
        artifact_path="model",
        input_example=input_example
    )
   
    # Log metrics manual tambahan (jika diperlukan)
    accuracy = model.score(X_test, y_test)
    mlflow.log_metric("test_accuracy", accuracy)
    
    print(f"✅ Model XGBoost berhasil dilatih dan dilog ke MLflow!")
    print(f"📊 Akurasi pada data test: {accuracy:.4f}")