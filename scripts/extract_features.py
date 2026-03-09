import os
import cv2
import numpy as np
import mysql.connector

# ======================
# MySQL CONNECTION
# ======================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="esgogiknem1",  # <-- փոխիր քո password-ով
    database="fire_smoke_db"
)

cursor = conn.cursor()

# ======================
# CLEAN TABLE FIRST
# ======================
print("Deleting all existing rows in frames table...")
cursor.execute("DELETE FROM frames;")
conn.commit()
print("All rows deleted.")

# ======================
# DATASET PATH
# ======================

dataset_path = "data/train/images"

insert_count = 0

# ======================
# LOOP THROUGH IMAGES
# ======================
image_files = os.listdir(dataset_path)[:100]
for file in image_files:
    print("Processing:", file)

    if file.endswith(".jpg") or file.endswith(".png"):

        path = os.path.join(dataset_path, file)

        img = cv2.imread(path)

        if img is None:
            continue

        # Resolution
        height, width, _ = img.shape
        resolution = f"{width}x{height}"

        # File size in KB
        frame_size_kb = os.path.getsize(path) / 1024

        # Brightness
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)

        # Blur score (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Simulated motion level
        motion_level = np.random.rand()

        # Camera ID detection from filename
        
        file_lower = file.lower()
        if file_lower.startswith("aof"):
            camera_id = "camera_1"
        elif file_lower.startswith("publicdataset"):
            camera_id = "camera_2"
        elif file_lower.startswith("web"):
            camera_id = "camera_3"
        else:
            camera_id = "unknown"

        # Insert into DB
        sql = """
        INSERT INTO frames 
        (file_name, file_path, frame_size_kb, resolution, brightness, blur_score, motion_level, camera_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            file,
            path,
            frame_size_kb,
            resolution,
            brightness,
            blur_score,
            motion_level,
            camera_id
        ))

        insert_count += 1

# Commit changes
conn.commit()

# Close connection
conn.close()

print(f"Inserted {insert_count} images into database successfully!")