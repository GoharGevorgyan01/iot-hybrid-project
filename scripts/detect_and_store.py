import os
from ultralytics import YOLO
import mysql.connector

# -----------------------------
# SETTINGS
# -----------------------------
MODEL_PATH = r"C:\Users\User\Desktop\project\model\weights\yolov8s_best.pt"
IMAGE_DIR = r"C:\Users\User\Documents\hmo\tez\smoke-fire-dataset\data\test\images"
MIN_CONFIDENCE = 0.40

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "esgogiknem1",
    "database": "fire_smoke_db"
}

CLASS_MAP = {
    0: "smoke",
    1: "fire"
}

# -----------------------------
# LOAD MODEL
# -----------------------------
print("Loading YOLO model...")
model = YOLO(MODEL_PATH)

# -----------------------------
# CONNECT TO MYSQL
# -----------------------------
print("Connecting to MySQL...")
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# -----------------------------
# PROCESS IMAGES
# -----------------------------
image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

print(f"Found {len(image_files)} images.")

inserted_count = 0

for file_name in image_files:
    image_path = os.path.join(IMAGE_DIR, file_name)
    print(f"Processing: {file_name}")

    # find matching frame_id in frames table
    cursor.execute("SELECT frame_id FROM frames WHERE file_name = %s", (file_name,))
    row = cursor.fetchone()

    if not row:
        print(f"Skipping {file_name} - frame_id not found in database")
        continue

    frame_id = row[0]

    # optional: old detections for same frame can be removed
    cursor.execute("DELETE FROM detections WHERE frame_id = %s", (frame_id,))

    # run inference
    results = model(image_path, verbose=False)

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            if confidence < MIN_CONFIDENCE:
                continue
            xywh = box.xywh[0].tolist()

            object_type = CLASS_MAP.get(class_id, "unknown")

            bbox_x = float(xywh[0])
            bbox_y = float(xywh[1])
            bbox_width = float(xywh[2])
            bbox_height = float(xywh[3])

            cursor.execute("""
                INSERT INTO detections
                (frame_id, object_type, confidence, bbox_x, bbox_y, bbox_width, bbox_height)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                frame_id,
                object_type,
                confidence,
                bbox_x,
                bbox_y,
                bbox_width,
                bbox_height
            ))

            inserted_count += 1

conn.commit()
cursor.close()
conn.close()

print(f"Done. Inserted {inserted_count} detections into database.")