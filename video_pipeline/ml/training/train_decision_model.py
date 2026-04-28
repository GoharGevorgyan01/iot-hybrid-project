import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier


# ==============================
# Paths
# ==============================
DATASET_PATH = "video_pipeline/ml/event_dataset_labeled.csv"
MODEL_PATH = "video_pipeline/ml/final_xgboost_model.pkl"
ENCODER_PATH = "video_pipeline/ml/label_encoder.pkl"


# ==============================
# ML Features (FINAL)
# ==============================
FEATURES = [
    "max_confidence",
    "avg_confidence",
    "object_count",
    "fire_smoke_ratio",
    "bbox_area_ratio",
    "detection_density_5s",
    "detection_density_10s",
    "avg_confidence_5s",
    "consecutive_fire_ratio",
    "bbox_area_growth",
    "brightness",
    "blur_score",
    "motion_level",
]


# ==============================
# Load dataset
# ==============================
def load_dataset():
    df = pd.read_csv(DATASET_PATH)

    X = df[FEATURES]
    y = df["transmission_decision"]

    encoder = LabelEncoder()
    y_enc = encoder.fit_transform(y)

    return X, y_enc, encoder


# ==============================
# Train models
# ==============================
def train_models(X_train, y_train):
    # Logistic Regression needs scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    models = {
        "LogReg": (
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced"
            ),
            X_train_scaled
        ),

        "RandomForest": (
            RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                class_weight="balanced",
                random_state=42
            ),
            X_train
        ),

        "XGBoost": (
            XGBClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="multi:softprob",
                eval_metric="mlogloss",
                random_state=42
            ),
            X_train
        )
    }

    trained_models = {}

    for name, (model, data) in models.items():
        model.fit(data, y_train)
        trained_models[name] = (model, scaler if name == "LogReg" else None)

    return trained_models


# ==============================
# Evaluate models
# ==============================
def evaluate_models(models, X_test, y_test, encoder):
    scaler = StandardScaler()
    X_test_scaled = scaler.fit_transform(X_test)

    for name, (model, model_scaler) in models.items():

        if name == "LogReg":
            preds = model.predict(X_test_scaled)
        else:
            preds = model.predict(X_test)

        print("\n============================")
        print(f"MODEL: {name}")

        print("\nClassification Report:")
        print(classification_report(
            y_test,
            preds,
            target_names=encoder.classes_
        ))

        print("Confusion Matrix:")
        print(confusion_matrix(y_test, preds))


# ==============================
# Main
# ==============================
def main():
    X, y, encoder = load_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y
    )

    models = train_models(X_train, y_train)
    evaluate_models(models, X_test, y_test, encoder)

    # Save final best model (XGBoost)
    joblib.dump(models["XGBoost"][0], MODEL_PATH)
    joblib.dump(encoder, ENCODER_PATH)

    print(f"\n✅ Final model saved to {MODEL_PATH}")
    print(f"✅ Label encoder saved to {ENCODER_PATH}")


if __name__ == "__main__":
    main()