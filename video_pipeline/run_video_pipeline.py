import os
import cv2
import time
import psutil
from ultralytics import YOLO

# DB imports
from db.db_connection import get_connection
from db.insert_functions import (
    insert_video,
    insert_frame,
    insert_detection,
    insert_performance_metrics
)

# Feature extraction helpers
from utils import (
    compute_brightness,
    compute_blur,
    compute_resolution,
    compute_file_size_kb,
    compute_motion
)

MODEL_PATH = "model/runs/yolov8n_quick_test/weights/best.pt"
INPUT_DIR = "video_pipeline/input"
SAVE_DIR = "video_pipeline/output/saved_frames"

CONF_THRESHOLD = 0.25
FRAME_SKIP = 1  # process every frame

# Current Python process for RAM usage
PROCESS = psutil.Process()


def get_video_files(input_dir):
    """Get all supported video files from input directory."""
    supported_extensions = (".mp4", ".avi", ".mov", ".mkv")
    return [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith(supported_extensions)
    ]


def process_video(video_path, model, cursor, conn):
    """Process one video and save important frames + detections + metrics."""
    video_file_name = os.path.basename(video_path)

    # Extract camera_id from filename
    camera_id = video_file_name.split("_")[0]

    print(f"\n🎬 Processing video: {video_file_name}")
    print(f"📷 Camera ID: {camera_id}")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"❌ Cannot open video: {video_file_name}")
        return

    # Read basic video metadata
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps > 0 else 0

    print(f"📊 FPS: {fps}")
    print(f"📊 Total frames: {total_frames}")

    # Insert one row for current video
    video_id = insert_video(
        cursor,
        video_name=video_file_name,
        camera_name=camera_id,
        video_path=video_path,
        duration_sec=duration_sec,
        fps=fps,
        total_frames=total_frames
    )
    conn.commit()

    print(f"🗂️ Video inserted with ID: {video_id}")

    frame_index = 0
    saved_count = 0
    prev_frame = None  # store previous frame for motion calculation

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_index += 1

        # Start full frame processing timer
        frame_start_time = time.perf_counter()

        # Skip frames if needed
        if frame_index % FRAME_SKIP != 0:
            continue

        # Measure YOLO inference time
        inference_start = time.perf_counter()
        results = model(frame, conf=CONF_THRESHOLD)
        inference_ms = (time.perf_counter() - inference_start) * 1000

        frame_has_detection = False

        # Check if frame contains fire or smoke
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                class_name = model.names[cls_id]

                print(f"Frame {frame_index}: {class_name} ({conf:.2f})")

                if class_name in ["fire", "smoke"]:
                    frame_has_detection = True

        # Save only important frames
        if frame_has_detection:
            file_name = f"{camera_id}_frame_{frame_index}.jpg"
            output_path = os.path.join(SAVE_DIR, file_name)

            # Draw boxes and labels
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue

                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    class_name = model.names[cls_id]

                    if class_name in ["fire", "smoke"]:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                        # Draw bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

                        # Draw label text
                        label = f"{class_name} {conf:.2f}"
                        cv2.putText(
                            frame,
                            label,
                            (x1, max(y1 - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 0, 255),
                            2
                        )

            # Save annotated frame
            cv2.imwrite(output_path, frame)

            # Feature extraction
            brightness = compute_brightness(frame)
            blur_score = compute_blur(frame)
            resolution = compute_resolution(frame)
            frame_size_kb = compute_file_size_kb(output_path)
            motion_level = compute_motion(prev_frame, frame)

            print(
                "FEATURE DEBUG:",
                file_name,
                brightness,
                blur_score,
                motion_level,
                resolution,
                frame_size_kb
            )

            # Start DB insert timer
            db_start = time.perf_counter()

            # Insert frame metadata
            frame_id = insert_frame(
                cursor,
                video_id,
                file_name,
                output_path,
                camera_id,
                frame_size_kb,
                resolution,
                brightness,
                blur_score,
                motion_level
            )

            # Insert detections
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue

                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    class_name = model.names[cls_id]

                    if class_name in ["fire", "smoke"]:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()

                        insert_detection(
                            cursor,
                            frame_id,
                            class_name,
                            conf,
                            x1,
                            y1,
                            x2 - x1,
                            y2 - y1
                        )

            # Measure performance metrics
            db_insert_ms = (time.perf_counter() - db_start) * 1000
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_mb = PROCESS.memory_info().rss / (1024 * 1024)
            processing_ms = (time.perf_counter() - frame_start_time) * 1000

            print(
                "PERF DEBUG:",
                f"inference={inference_ms:.2f}ms,",
                f"processing={processing_ms:.2f}ms,",
                f"db={db_insert_ms:.2f}ms,",
                f"cpu={cpu_percent:.2f}%,",
                f"ram={memory_mb:.2f}MB"
            )

            # Insert performance metrics
            insert_performance_metrics(
                cursor,
                frame_id,
                inference_ms,
                processing_ms,
                db_insert_ms,
                cpu_percent,
                memory_mb
            )

            conn.commit()
            saved_count += 1

            print(f"💾 Saved + inserted: {file_name}")

            # Update previous frame for motion calculation
            prev_frame = frame.copy()

    cap.release()
    print(f"✅ Finished {video_file_name} | Saved frames: {saved_count}")


def main():
    """Main pipeline: process all videos in input folder."""
    os.makedirs(SAVE_DIR, exist_ok=True)

    print("🔄 Loading YOLO model...")
    model = YOLO(MODEL_PATH)

    conn = get_connection()
    cursor = conn.cursor()

    video_files = get_video_files(INPUT_DIR)

    if not video_files:
        print("❌ No videos found.")
        cursor.close()
        conn.close()
        return

    print(f"📁 Found {len(video_files)} video(s)")

    for video_path in video_files:
        process_video(video_path, model, cursor, conn)

    cursor.close()
    conn.close()

    print("\n✅ All videos processed successfully.")


if __name__ == "__main__":
    main()