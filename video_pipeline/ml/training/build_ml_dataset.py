import os
import re
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Add video_pipeline folder to Python path
CURRENT_FILE = Path(__file__).resolve()
VIDEO_PIPELINE_DIR = CURRENT_FILE.parents[1]
sys.path.insert(0, str(VIDEO_PIPELINE_DIR))


from video_pipeline.db.db_connection import get_connection

OUTPUT_PATH = VIDEO_PIPELINE_DIR / "ml" / "training" / "event_dataset_raw.csv"

WINDOW_SEC = 5
STEP_SEC = 1


FEATURE_COLUMNS = [
    "max_confidence",
    "avg_confidence",
    "object_count",
    "fire_smoke_ratio",
    "bbox_area_ratio",
    "detection_density_5s",
    "detection_density_10s",
    "avg_confidence_5s",
    "consecutive_fire_ratio",
    "bbox_area_growth",
    "brightness",
    "blur_score",
    "motion_level",
]


def load_tables():
    """Load required MySQL tables into pandas DataFrames."""
    conn = get_connection()

    videos_df = pd.read_sql("SELECT * FROM videos", conn)
    frames_df = pd.read_sql("SELECT * FROM frames", conn)
    detections_df = pd.read_sql("SELECT * FROM detections", conn)

    conn.close()

    print("Videos:", videos_df.shape)
    print("Frames:", frames_df.shape)
    print("Detections:", detections_df.shape)

    return videos_df, frames_df, detections_df


def extract_frame_number(file_name):
    """Extract frame number from file name like cam01_frame_77.jpg."""
    match = re.search(r"frame_(\d+)", file_name)
    return int(match.group(1)) if match else None


def parse_resolution(resolution):
    """Parse resolution string WIDTHxHEIGHT."""
    if pd.isna(resolution):
        return None, None

    try:
        width, height = resolution.lower().split("x")
        return int(width), int(height)
    except Exception:
        return None, None


def build_frame_level_dataset(videos_df, frames_df, detections_df):
    """Aggregate detections so each frame becomes one row."""

    # Compute bbox area
    detections_df["bbox_area"] = (
        detections_df["bbox_width"] * detections_df["bbox_height"]
    )

    # Aggregate detections per frame
    detection_agg = (
        detections_df
        .groupby("frame_id")
        .agg(
            max_confidence=("confidence", "max"),
            avg_confidence=("confidence", "mean"),
            object_count=("detection_id", "count"),
            fire_count=("object_type", lambda x: (x == "fire").sum()),
            smoke_count=("object_type", lambda x: (x == "smoke").sum()),
            max_bbox_area=("bbox_area", "max"),
            avg_bbox_area=("bbox_area", "mean"),
        )
        .reset_index()
    )

    # Merge frame metadata with detection aggregation
    frame_df = frames_df.merge(detection_agg, on="frame_id", how="left")

    # Merge video metadata
    frame_df = frame_df.merge(
        videos_df[["video_id", "video_name", "camera_name", "fps", "duration_sec"]],
        on="video_id",
        how="left"
    )

    # Extract frame number from file name
    frame_df["frame_number"] = frame_df["file_name"].apply(extract_frame_number)

    # Compute timestamp inside video
    frame_df["timestamp_sec"] = frame_df["frame_number"] / frame_df["fps"]

    # Parse resolution
    frame_df[["frame_width", "frame_height"]] = frame_df["resolution"].apply(
        lambda x: pd.Series(parse_resolution(x))
    )

    # Compute frame area
    frame_df["frame_area"] = frame_df["frame_width"] * frame_df["frame_height"]

    # Normalize bbox area
    frame_df["bbox_area_ratio"] = (
        frame_df["max_bbox_area"] / frame_df["frame_area"]
    )

    # Compute fire/smoke ratio
    total_fire_smoke = frame_df["fire_count"] + frame_df["smoke_count"]
    frame_df["fire_smoke_ratio"] = np.where(
        total_fire_smoke > 0,
        frame_df["fire_count"] / total_fire_smoke,
        0
    )

    # Fill missing numeric values
    numeric_cols = [
        "max_confidence",
        "avg_confidence",
        "object_count",
        "fire_count",
        "smoke_count",
        "max_bbox_area",
        "avg_bbox_area",
        "bbox_area_ratio",
        "fire_smoke_ratio",
        "brightness",
        "blur_score",
        "motion_level",
    ]

    frame_df[numeric_cols] = frame_df[numeric_cols].fillna(0)

    print("Frame-level dataset:", frame_df.shape)

    return frame_df


def max_consecutive_fire_frames(window_df):
    window_df = window_df.sort_values("timestamp_sec")

    """Compute maximum consecutive frames with fire detections."""
    fire_flags = (window_df["fire_count"] > 0).astype(int).tolist()

    max_run = 0
    current_run = 0

    for flag in fire_flags:
        if flag == 1:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0

    return max_run


def build_event_dataset(frame_df):
    """Build event-level dataset using sliding time windows."""
    events = []

    for video_id, video_df in frame_df.groupby("video_id"):
        video_df = video_df.sort_values("timestamp_sec").reset_index(drop=True)

        video_name = video_df["video_name"].iloc[0]
        camera_name = video_df["camera_name"].iloc[0]
        fps = video_df["fps"].iloc[0]
        duration_sec = video_df["duration_sec"].iloc[0]

        start_time = 0

        while start_time + WINDOW_SEC <= duration_sec:
            end_time = start_time + WINDOW_SEC

            # Main 5s event window
            window_5s = video_df[
                (video_df["timestamp_sec"] >= start_time) &
                (video_df["timestamp_sec"] < end_time)
            ]

            # 10s lookback window for temporal stability
            lookback_start = max(0, end_time - 10)
            window_10s = video_df[
                (video_df["timestamp_sec"] >= lookback_start) &
                (video_df["timestamp_sec"] < end_time)
            ]

            if len(window_5s) == 0:
                start_time += STEP_SEC
                continue

            frames_in_5s = max(fps * 5, 1)
            frames_in_10s = max(fps * 10, 1)

            fire_total = window_5s["fire_count"].sum()
            smoke_total = window_5s["smoke_count"].sum()
            total_fire_smoke = fire_total + smoke_total

            # Select representative frame with highest confidence
            best_frame = window_5s.loc[window_5s["max_confidence"].idxmax()]

            representative_frame_id = best_frame["frame_id"]
            representative_frame_name = best_frame["file_name"]
            representative_frame_path = best_frame["file_path"]

            bbox_first = window_5s["bbox_area_ratio"].iloc[0]
            bbox_last = window_5s["bbox_area_ratio"].iloc[-1]

            if bbox_first > 0:
                bbox_growth = (bbox_last - bbox_first) / bbox_first
            else:
                bbox_growth = 0

            # Compute consecutive fire frames
            consecutive_frames = max_consecutive_fire_frames(window_5s)

            event = {
                "video_id": video_id,
                "video_name": video_name,
                "camera_name": camera_name,
                "window_start_sec": start_time,
                "window_end_sec": end_time,

                # Representative frame for SEND_FULL upload
                "representative_frame_id": representative_frame_id,
                "representative_frame_name": representative_frame_name,
                "representative_frame_path": representative_frame_path,

                # Detection features
                "max_confidence": window_5s["max_confidence"].max(),
                "avg_confidence": window_5s["avg_confidence"].mean(),
                "object_count": window_5s["object_count"].mean(),
                "fire_smoke_ratio": fire_total / total_fire_smoke if total_fire_smoke > 0 else 0,
                "bbox_area_ratio": window_5s["bbox_area_ratio"].max(),

                # Temporal features
                "detection_density_5s": window_5s["object_count"].sum() / frames_in_5s,
                "detection_density_10s": window_10s["object_count"].sum() / frames_in_10s,
                "avg_confidence_5s": window_5s["avg_confidence"].mean(),
                "consecutive_fire_ratio": consecutive_frames / (fps * 5),
                "bbox_area_growth": bbox_growth,

                # Frame quality features
                "brightness": window_5s["brightness"].mean(),
                "blur_score": window_5s["blur_score"].mean(),
                "motion_level": window_5s["motion_level"].mean(),
            }

            events.append(event)
            start_time += STEP_SEC

    event_df = pd.DataFrame(events)

    print("Event-level dataset:", event_df.shape)

    return event_df

def clean_event_dataset(event_df):
    """Apply initial cleaning to event-level dataset."""

    # Replace infinities with NaN
    event_df = event_df.replace([np.inf, -np.inf], np.nan)

    # Fill missing values
    event_df[FEATURE_COLUMNS] = event_df[FEATURE_COLUMNS].fillna(0)
    # 🔥 CLIP extreme bbox growth values
    event_df["bbox_area_growth"] = event_df["bbox_area_growth"].clip(-1, 3)

    # Clip invalid values
    event_df["bbox_area_ratio"] = event_df["bbox_area_ratio"].clip(0, 1)
    event_df["fire_smoke_ratio"] = event_df["fire_smoke_ratio"].clip(0, 1)

    return event_df


def save_dataset(event_df):
    """Save ML event dataset to CSV."""
    os.makedirs(OUTPUT_PATH.parent, exist_ok=True)
    event_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved dataset to: {OUTPUT_PATH}")


def print_summary(event_df):
    """Print dataset summary for thesis screenshots."""
    print("\nDataset columns:")
    print(event_df.columns.tolist())

    print("\nFeature summary:")
    print(event_df[FEATURE_COLUMNS].describe().round(3))

    print("\nEvents per video:")
    print(event_df.groupby("video_name").size())


if __name__ == "__main__":
    videos_df, frames_df, detections_df = load_tables()

    frame_df = build_frame_level_dataset(
        videos_df,
        frames_df,
        detections_df
    )

    event_df = build_event_dataset(frame_df)
    event_df = clean_event_dataset(event_df)

    print_summary(event_df)
    save_dataset(event_df)