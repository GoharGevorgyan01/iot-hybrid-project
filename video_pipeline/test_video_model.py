import os
from ultralytics import YOLO

MODEL_PATH = "model/runs/yolov8n_quick_test/weights/best.pt"
VIDEO_PATH = "video_pipeline/input/car_fire.mp4"
OUTPUT_DIR = os.path.abspath("video_pipeline/output")


def main():
    print("🔄 Loading YOLO model...")
    model = YOLO(MODEL_PATH)

    print("🎬 Running inference on video...")
    model.predict(
        source=VIDEO_PATH,
        save=True,
        project=OUTPUT_DIR,   
        name="results",
        conf=0.25,
        exist_ok=True         
    )

    print("✅ Inference finished.")
    print(f"📁 Results saved in: {OUTPUT_DIR}/results")


if __name__ == "__main__":
    main()