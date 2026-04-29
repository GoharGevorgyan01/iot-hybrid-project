import os
import cv2
import numpy as np
import mysql.connector

# ======================
# CONFIG
# ======================

DATASET_ROOT = r"C:\Users\User\Documents\hmo\tez\smoke-fire-dataset\data"
SUBSETS = ["train", "val", "test"]
LIMIT_PER_SUBSET = None   # սկզբում test-ի համար փոքր պահենք, հետո կարող ես մեծացնել կամ None անել

# ======================
# MYSQL CONNECTION
# ======================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="esgogiknem1",
    database="fire_smoke_db"
)

cursor = conn.cursor()

# ======================
# ENSURE CAMERAS EXIST
# ======================

camera_rows = [
    ("camera_1", "AoF_Source", 30, "active"),
    ("camera_2", "PublicDataset_Source", 25, "active"),
    ("camera_3", "WEB_Source", 20, "active"),
    ("camera_unknown", "Unknown_Source", 15, "inactive")
]

camera_insert_sql = """
INSERT IGNORE INTO cameras (camera_id, location, fps, status)
VALUES (%s, %s, %s, %s)
"""

cursor.executemany(camera_insert_sql, camera_rows)
conn.commit()

# ======================
# CLEAN FRAMES TABLE
# ======================

print("Deleting old rows from frames table...")
cursor.execute("DELETE FROM frames")
cursor.execute("ALTER TABLE frames AUTO_INCREMENT = 1")
conn.commit()
print("Old rows deleted and AUTO_INCREMENT reset.")

# ======================
# INSERT SQL
# ======================

insert_sql = """
INSERT INTO frames
(file_name, file_path, frame_size_kb, resolution, brightness, blur_score, motion_level, camera_id, dataset_split)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

insert_count = 0

# ======================
# LOOP THROUGH DATASET
# ======================

for subset in SUBSETS:
    images_path = os.path.join(DATASET_ROOT, subset, "images")

    if not os.path.exists(images_path):
        print(f"Path not found: {images_path}")
        continue

    image_files = [
        f for f in os.listdir(images_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if LIMIT_PER_SUBSET is not None:
        image_files = image_files[:LIMIT_PER_SUBSET]

    print(f"\nProcessing subset: {subset}")
    print(f"Found {len(image_files)} image files")

    for file in image_files:
        path = os.path.join(images_path, file)
        img = cv2.imread(path)

        if img is None:
            print(f"Skipped unreadable file: {file}")
            continue

        # Resolution
        height, width, _ = img.shape
        resolution = f"{width}x{height}"

        # File size in KB
        frame_size_kb = os.path.getsize(path) / 1024.0

        # Brightness
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))

        # Blur score
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # Simulated motion level
        motion_level = float(np.random.uniform(0.0, 1.0))

        # Camera mapping by filename
        file_lower = file.lower()
        if file_lower.startswith("aof"):
            camera_id = "camera_1"
        elif file_lower.startswith("publicdataset"):
            camera_id = "camera_2"
        elif file_lower.startswith("web"):
            camera_id = "camera_3"
        else:
            camera_id = "camera_unknown"

        cursor.execute(
            insert_sql,
            (
                file,
                path,
                frame_size_kb,
                resolution,
                brightness,
                blur_score,
                motion_level,
                camera_id,
                subset
            )
        )

        insert_count += 1

conn.commit()
conn.close()

print(f"\nInserted {insert_count} frames into database successfully.")