import os
import sqlite3
from pathlib import Path

DATASET_PATH = Path("dataset/train")
IMAGES_PATH = DATASET_PATH / "images"
LABELS_PATH = DATASET_PATH / "labels"

conn = sqlite3.connect("dataset.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS frames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frame_id INTEGER,
    class_id INTEGER,
    x_center REAL,
    y_center REAL,
    width REAL,
    height REAL
)
""")

for label_file in LABELS_PATH.glob("*.txt"):

    image_name = label_file.stem + ".jpg"

    cursor.execute(
        "INSERT INTO frames (filename) VALUES (?)",
        (image_name,)
    )

    frame_id = cursor.lastrowid

    with open(label_file, "r") as f:
        for line in f:

            parts = line.strip().split()

            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])

            cursor.execute("""
            INSERT INTO detections
            (frame_id, class_id, x_center, y_center, width, height)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (frame_id, class_id, x_center, y_center, width, height))

conn.commit()
conn.close()

print("Dataset ingestion complete")