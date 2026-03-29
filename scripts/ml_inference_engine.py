import json
import joblib
import pandas as pd
import mysql.connector
from datetime import datetime
from decimal import Decimal
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from edge.publisher.aws_iot_publisher import publish_payload

# =========================================
# MySQL database connection settings
# Քո password-ը այստեղ փոխիր
# =========================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "esgogiknem1",
    "database": "fire_smoke_db"
}

# =========================================
# Trained model-երի paths
# Այստեղից script-ը բեռնում է արդեն train արված .pkl model-երը
# =========================================
PRIORITY_MODEL_PATH = "model/ml/priority_model.pkl"
ACTION_MODEL_PATH = "model/ml/action_model.pkl"
QOS_MODEL_PATH = "model/ml/qos_model.pkl"

# =========================================
# Feature columns for priority prediction
# Սրանք պիտի լինեն ճիշտ այն same columns-երը,
# որոնցով train արել ես priority_model-ը
# =========================================
PRIORITY_FEATURES = [
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
    "bandwidth_usage_kb",
    "qos_level"
]

# =========================================
# Feature columns for transmission action prediction
# Քանի որ action_model-ի train-ի ժամանակ էլ նույն feature-ներն են օգտագործվել,
# այստեղ նույն list-ն է
# =========================================
ACTION_FEATURES = [
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
    "bandwidth_usage_kb",
    "qos_level"
]

# =========================================
# Feature columns for QoS prediction
# Այստեղ qos_level չկա, որովհետև սա հենց predict անելու target-ն էր
# =========================================
QOS_FEATURES = [
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


# =========================================
# Function: load trained ML models
# Նպատակ՝ .pkl ֆայլերից model-երը բեռնել հիշողություն
# =========================================
def load_models():
    priority_model = joblib.load(PRIORITY_MODEL_PATH)
    action_model = joblib.load(ACTION_MODEL_PATH)
    qos_model = joblib.load(QOS_MODEL_PATH)
    return priority_model, action_model, qos_model

def convert_decimal(obj):
    """
    Եթե obj-ը Decimal type է, դարձնում ենք float,
    որ հնարավոր լինի JSON-ի մեջ տպել։
    """
    if isinstance(obj, Decimal):
        return float(obj)
    return obj
# =========================================
# Function: fetch latest frame data from MySQL
# Նպատակ՝ DB-ից վերցնել ամենավերջին frame-ի տվյալները
# և detections/network_metrics-ի հիման վրա սարքել input features
# =========================================
def fetch_latest_frame_features():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        f.frame_id,
        f.file_name,
        f.camera_id,
        f.frame_size_kb,
        f.brightness,
        f.blur_score,
        f.motion_level,

        nm.latency_ms,
        nm.packet_loss,
        nm.bandwidth_usage_kb,
        nm.qos_level,

        COALESCE(SUM(CASE WHEN d.object_type = 'fire' THEN 1 ELSE 0 END), 0) AS fire_count,
        COALESCE(SUM(CASE WHEN d.object_type = 'smoke' THEN 1 ELSE 0 END), 0) AS smoke_count,
        COALESCE(COUNT(d.detection_id), 0) AS total_detected_objects,
        COALESCE(MAX(d.confidence), 0) AS max_confidence

    FROM frames f
    LEFT JOIN detections d ON f.frame_id = d.frame_id
    LEFT JOIN network_metrics nm ON f.frame_id = nm.frame_id

    GROUP BY
        f.frame_id, f.file_name, f.camera_id,
        f.frame_size_kb, f.brightness, f.blur_score, f.motion_level,
        nm.latency_ms, nm.packet_loss, nm.bandwidth_usage_kb, nm.qos_level

    ORDER BY f.frame_id DESC
    LIMIT 1
    """

    cursor.execute(query)
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row


# =========================================
# Function: prepare input dataframe for one model
# Նպատակ՝ row dictionary-ից վերցնել միայն պետքական columns-ը
# և դարձնել pandas DataFrame
#
# Օրինակ՝ priority model-ի համար վերցնում է միայն PRIORITY_FEATURES
# =========================================
def prepare_model_input(row, feature_columns):
    data = {}

    for col in feature_columns:
        data[col] = row[col]

    return pd.DataFrame([data])


# =========================================
# Function: build final JSON payload
# Նպատակ՝ prediction-ներն ու input feature-երը դնել մեկ միասնական JSON structure-ի մեջ
#
# Սա հետո կարող ենք ուղարկել MQTT/AWS IoT-ին
# =========================================
def build_payload(row, priority_pred, action_pred, qos_pred):
    payload = {
        "frame_id": int(row["frame_id"]),
        "file_name": row["file_name"],
        "camera_id": row["camera_id"],
        "timestamp": datetime.now().isoformat(),

        "features": {
            "fire_count": int(convert_decimal(row["fire_count"])),
            "smoke_count": int(convert_decimal(row["smoke_count"])),
            "total_detected_objects": int(convert_decimal(row["total_detected_objects"])),
            "max_confidence": float(convert_decimal(row["max_confidence"])),
            "motion_level": float(convert_decimal(row["motion_level"])),
            "frame_size_kb": float(convert_decimal(row["frame_size_kb"])),
            "brightness": float(convert_decimal(row["brightness"])),
            "blur_score": float(convert_decimal(row["blur_score"])),
            "latency_ms": float(convert_decimal(row["latency_ms"])),
            "packet_loss": float(convert_decimal(row["packet_loss"])),
            "bandwidth_usage_kb": float(convert_decimal(row["bandwidth_usage_kb"])),
            "qos_level": int(convert_decimal(row["qos_level"]))
        },

        "predictions": {
            "priority_level": str(priority_pred),
            "transmission_action": str(action_pred),
            "selected_qos": int(qos_pred)
        }
    }

    return payload

def save_prediction_to_db(row, priority_pred, action_pred, qos_pred, payload):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    query = """
    INSERT INTO ml_predictions (
        frame_id,
        predicted_priority,
        predicted_action,
        predicted_qos,
        payload_json
    )
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        int(row["frame_id"]),
        str(priority_pred),
        str(action_pred),
        int(qos_pred),
        json.dumps(payload)
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()
# =========================================
# Main function
# Ամբողջ inference flow-ը այստեղ է
# =========================================
def main():
    # 1) Load trained models
    print("Loading models...")
    priority_model, action_model, qos_model = load_models()

    # 2) Fetch latest frame data from DB
    print("Fetching latest frame data from MySQL...")
    row = fetch_latest_frame_features()

    # Եթե տվյալ չկա՝ կանգնում ենք
    if not row:
        print("No data found in database.")
        return

    # 3) Prepare separate inputs for each model
    print("Preparing model inputs...")
    X_priority = prepare_model_input(row, PRIORITY_FEATURES)
    X_action = prepare_model_input(row, ACTION_FEATURES)
    X_qos = prepare_model_input(row, QOS_FEATURES)

    # 4) Run predictions
    print("Running ML inference...")
    priority_pred = priority_model.predict(X_priority)[0]
    action_pred = action_model.predict(X_action)[0]
    qos_pred = qos_model.predict(X_qos)[0]

    # 5) Build final payload
    payload = build_payload(row, priority_pred, action_pred, qos_pred)
    save_prediction_to_db(row, priority_pred, action_pred, qos_pred, payload)
    publish_payload(payload)
    print("Payload published to AWS IoT Core.")
    print("Prediction saved to ml_predictions table.")

    # 6) Print JSON payload
    print("\nJSON Payload:")
    print(json.dumps(payload, indent=4))

    # 7) Print simple log line
    print("\nLog:")
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"frame_id={row['frame_id']} | "
        f"priority={priority_pred} | "
        f"action={action_pred} | "
        f"qos={qos_pred}"
    )


# =========================================
# Script entry point
# Երբ այս file-ը run ես անում, այստեղից է սկսվում
# =========================================
if __name__ == "__main__":
    main()