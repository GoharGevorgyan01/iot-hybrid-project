import os
import time
import runpy
from pathlib import Path

from video_pipeline.ml.inference.metrics_exporter import start_metrics_server
from video_pipeline import run_video_pipeline
from video_pipeline.ml.inference import run_pipeline_on_videos


PROJECT_ROOT = Path(__file__).resolve().parent


def run_script_step(title, relative_script_path):
    """Run a Python script file as __main__."""
    print("\n==============================")
    print(f"▶ {title}")
    print("==============================")

    script_path = PROJECT_ROOT / relative_script_path

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    runpy.run_path(str(script_path), run_name="__main__")


def main():
    # One Prometheus endpoint for the full end-to-end run
    start_metrics_server(port=8000)

    print("\n==============================")
    print("▶ Step 1: YOLO video processing and MySQL insert")
    print("==============================")
    run_video_pipeline.main()

    run_script_step(
        "Step 2: Build event-level dataset",
        "video_pipeline/ml/training/build_ml_dataset.py",
    )

    run_script_step(
        "Step 3: Generate rule-based labels",
        "video_pipeline/ml/training/generate_labels.py",
    )

    run_script_step(
        "Step 4: Train ML decision model",
        "video_pipeline/ml/training/train_decision_model.py",
    )

    print("\n==============================")
    print("▶ Step 5: ML inference, QoS, MQTT, S3 and Telegram")
    print("==============================")

    # Avoid starting /metrics endpoint twice
    os.environ["METRICS_SERVER_ALREADY_STARTED"] = "1"
    run_pipeline_on_videos.main()

    print("\n✅ Full monitored pipeline finished.")
    print("[Metrics] Keeping endpoint alive for Prometheus/Grafana.")
    print("[Metrics] Press Ctrl+C to stop.")

    while True:
        time.sleep(30)


if __name__ == "__main__":
    main()