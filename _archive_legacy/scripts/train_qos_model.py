import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# ---------------------------------
# PATHS
# ---------------------------------
DATASET_PATH = r"C:\Users\User\Desktop\project\results\ml_dataset\ml_dataset_all_targets.csv"

MODEL_DIR = r"C:\Users\User\Desktop\project\model\ml"
MODEL_PATH = os.path.join(MODEL_DIR, "qos_model.pkl")

os.makedirs(MODEL_DIR, exist_ok=True)

# ---------------------------------
# LOAD DATASET
# ---------------------------------
print("Reading ML dataset...")
df = pd.read_csv(DATASET_PATH)

print("Dataset shape:", df.shape)

# ---------------------------------
# FEATURE SELECTION
# ---------------------------------
FEATURE_COLUMNS = [
    "fire_count",
    "smoke_count",
    "total_detected_objects",
    "max_confidence",
    "motion_level",
    "frame_size_kb",
    "brightness",
    "blur_score",
    "latency_ms",
    "packet_loss",
    "bandwidth_usage_kb"
]

TARGET_COLUMN = "selected_qos"

# ---------------------------------
# SPLIT BY dataset_split
# ---------------------------------
train_df = df[df["dataset_split"] == "train"].copy()
val_df = df[df["dataset_split"] == "val"].copy()
test_df = df[df["dataset_split"] == "test"].copy()

print("\nSplit sizes:")
print("Train:", train_df.shape)
print("Val:", val_df.shape)
print("Test:", test_df.shape)

# ---------------------------------
# BUILD X AND y
# ---------------------------------
X_train = train_df[FEATURE_COLUMNS]
y_train = train_df[TARGET_COLUMN]

X_val = val_df[FEATURE_COLUMNS]
y_val = val_df[TARGET_COLUMN]

X_test = test_df[FEATURE_COLUMNS]
y_test = test_df[TARGET_COLUMN]

# ---------------------------------
# TRAIN MODEL
# ---------------------------------
print("\nTraining Random Forest classifier for selected_qos...")
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    class_weight="balanced"
)

model.fit(X_train, y_train)

# ---------------------------------
# VALIDATION EVALUATION
# ---------------------------------
print("\nEvaluating on validation set...")
val_preds = model.predict(X_val)

val_accuracy = accuracy_score(y_val, val_preds)
print("Validation Accuracy:", round(val_accuracy, 4))

print("\nValidation Classification Report:")
print(classification_report(y_val, val_preds, zero_division=0))

print("Validation Confusion Matrix:")
print(confusion_matrix(y_val, val_preds))

# ---------------------------------
# TEST EVALUATION
# ---------------------------------
print("\nEvaluating on test set...")
test_preds = model.predict(X_test)

test_accuracy = accuracy_score(y_test, test_preds)
print("Test Accuracy:", round(test_accuracy, 4))

print("\nTest Classification Report:")
print(classification_report(y_test, test_preds, zero_division=0))

print("Test Confusion Matrix:")
print(confusion_matrix(y_test, test_preds))

# ---------------------------------
# FEATURE IMPORTANCE
# ---------------------------------
print("\nFeature Importances:")
importances = model.feature_importances_

feature_importance_df = pd.DataFrame({
    "feature": FEATURE_COLUMNS,
    "importance": importances
}).sort_values(by="importance", ascending=False)

print(feature_importance_df)

# ---------------------------------
# SAVE MODEL
# ---------------------------------
joblib.dump(model, MODEL_PATH)
print("\nModel saved to:", MODEL_PATH)