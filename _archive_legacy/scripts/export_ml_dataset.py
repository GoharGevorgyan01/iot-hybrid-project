import os
import pandas as pd
import mysql.connector

# ---------------------------------
# DATABASE CONNECTION SETTINGS
# ---------------------------------
# Այստեղ գրում ենք MySQL-ի connection տվյալները
DB_CONFIG = {
    "host": "localhost",          # MySQL server-ը local machine-ի վրա է
    "user": "root",               # MySQL username
    "password": "esgogiknem1",  # քո MySQL password-ը
    "database": "fire_smoke_db"   # աշխատելու database-ը
}

# ---------------------------------
# OUTPUT FILE SETTINGS
# ---------------------------------
# Այստեղ որոշում ենք, թե dataset CSV-ն որտեղ պահել
OUTPUT_DIR = r"C:\Users\User\Desktop\project\results\ml_dataset"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "ml_dataset_all_targets.csv")

# եթե պանակը չկա, ստեղծում ենք
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------
# SQL QUERY FOR ML DATASET
# ---------------------------------
# Այս query-ն մեկ frame-ի համար բերում է.
# 1) frame features
# 2) detection summary
# 3) network metrics
# 4) decision labels (targets)
query = """
SELECT
    f.frame_id,
    f.file_name,
    f.dataset_split,          -- train / val / test
    f.frame_size_kb,
    f.resolution,
    f.brightness,
    f.blur_score,
    f.motion_level,

    -- detection summary features
    COALESCE(SUM(CASE WHEN d.object_type = 'fire' THEN 1 ELSE 0 END), 0) AS fire_count,
    COALESCE(SUM(CASE WHEN d.object_type = 'smoke' THEN 1 ELSE 0 END), 0) AS smoke_count,
    COALESCE(COUNT(d.detection_id), 0) AS total_detected_objects,
    COALESCE(MAX(d.confidence), 0) AS max_confidence,

    -- network features
    COALESCE(nm.latency_ms, 0) AS latency_ms,
    COALESCE(nm.packet_loss, 0) AS packet_loss,
    COALESCE(nm.bandwidth_usage_kb, 0) AS bandwidth_usage_kb,
    COALESCE(nm.qos_level, 0) AS qos_level,

    -- target labels from rule-based decision engine
    td.priority_level,
    td.transmission_action,
    td.selected_qos

FROM frames f
LEFT JOIN detections d
    ON f.frame_id = d.frame_id
LEFT JOIN network_metrics nm
    ON f.frame_id = nm.frame_id
LEFT JOIN transmission_decisions td
    ON f.frame_id = td.frame_id

GROUP BY
    f.frame_id,
    f.file_name,
    f.dataset_split,
    f.frame_size_kb,
    f.resolution,
    f.brightness,
    f.blur_score,
    f.motion_level,
    nm.latency_ms,
    nm.packet_loss,
    nm.bandwidth_usage_kb,
    nm.qos_level,
    td.priority_level,
    td.transmission_action,
    td.selected_qos
"""

# ---------------------------------
# CONNECT TO MYSQL
# ---------------------------------
print("Connecting to MySQL...")
conn = mysql.connector.connect(**DB_CONFIG)

# ---------------------------------
# READ SQL RESULT INTO PANDAS
# ---------------------------------
print("Reading data from database...")
df = pd.read_sql(query, conn)

# database connection-ը փակում ենք
conn.close()

# ---------------------------------
# BASIC CLEANING
# ---------------------------------
# պահում ենք միայն այն row-երը, որտեղ target-ները կան
df = df.dropna(subset=["priority_level", "transmission_action", "selected_qos"])

# selected_qos-ը integer դարձնենք
df["selected_qos"] = df["selected_qos"].astype(int)

# ---------------------------------
# SAVE CSV
# ---------------------------------
df.to_csv(OUTPUT_FILE, index=False)

print("Dataset exported successfully.")
print("Saved to:", OUTPUT_FILE)
print("Shape:", df.shape)

# split distribution
print("\nDataset split distribution:")
print(df["dataset_split"].value_counts())

# target distributions
print("\nPriority distribution:")
print(df["priority_level"].value_counts())

print("\nTransmission action distribution:")
print(df["transmission_action"].value_counts())

print("\nSelected QoS distribution:")
print(df["selected_qos"].value_counts())