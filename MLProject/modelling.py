import warnings
import mlflow
import mlflow.xgboost
import pandas as pd

from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

# ========================================
# Experiment
# ========================================
mlflow.set_experiment("Modelling_SML_Heart_Disease")

# Aktifkan Auto Logging
mlflow.autolog()

# ========================================
# Load Dataset
# ========================================
target_col = "num"

train_df = pd.read_csv("heart_disease_train.csv")
test_df = pd.read_csv("heart_disease_test.csv")

X_train = train_df.drop(columns=[target_col])
y_train = train_df[target_col].astype(int)

X_test = test_df.drop(columns=[target_col])
y_test = test_df[target_col].astype(int)

input_example = X_train.iloc[:5]

# ========================================
# Best Parameters
# ========================================
best_params = {
    "learning_rate": 0.01,
    "max_depth": 3,
    "n_estimators": 200,
    "subsample": 0.8,
    "random_state": 42,
}


model = XGBClassifier(**best_params)

# Training
model.fit(X_train, y_train)

# Prediction
y_pred = model.predict(X_test)

# Evaluation
accuracy = accuracy_score(y_test, y_pred)

# Log Metric
mlflow.log_metric("test_accuracy", accuracy)

# Save Model
mlflow.xgboost.log_model(
    xgb_model=model,
    artifact_path="model",
    input_example=input_example
)

print("=" * 50)
print("Training Finished Successfully")
print(f"Test Accuracy : {accuracy:.4f}")
print("=" * 50)
