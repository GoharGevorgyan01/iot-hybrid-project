import json
import pandas as pd
from pathlib import Path

from inference_engine import MLDecisionEngine
from network_policy import simulate_network_metrics, assign_qos


# ==============================
# Paths
# ==============================
BASE_DIR = Path(__file__).resolve().parents[3]

DATASET_PATH = BASE_DIR / "video_pipeline" / "ml" / "training" / "event_dataset_raw.csv"
LOG_PATH = BASE_DIR / "video_pipeline" / "ml" / "inference" / "decision_log.csv"
PAYLOAD_DIR = BASE_DIR / "video_pipeline" / "ml" / "inference" / "payloads"


# ==============================
# Final ML features
# ==============================
FEATURES = [
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


def build_metadata_payload(row, decision, qos, network_metrics):
    """Build compact JSON payload for metadata-only transmission."""
    return {
        "payload_type": "METADATA_ONLY",
        "video_name": row["video_name"],
        "camera_id": row["camera_name"],
        "window_start_sec": float(row["window_start_sec"]),
        "window_end_sec": float(row["window_end_sec"]),
        "ml_decision": decision,
        "qos": qos,
        "network": {
            "scenario": network_metrics["network_scenario"],
            "latency_ms": network_metrics["latency_ms"],
            "packet_loss": network_metrics["packet_loss"],
        },
        "event_summary": {
            "max_confidence": round(float(row["max_confidence"]), 3),
            "fire_smoke_ratio": round(float(row["fire_smoke_ratio"]), 3),
            "detection_density_5s": round(float(row["detection_density_5s"]), 3),
            "consecutive_fire_ratio": round(float(row["consecutive_fire_ratio"]), 3),
        },
        "image_sent": False,
    }


def build_full_payload(row, decision, qos, network_metrics, image_path):
    """Build full JSON payload for critical event transmission."""
    return {
        "payload_type": "FULL_EVENT",
        "video_name": row["video_name"],
        "camera_id": row["camera_name"],
        "window_start_sec": float(row["window_start_sec"]),
        "window_end_sec": float(row["window_end_sec"]),
        "ml_decision": decision,
        "qos": qos,
        "network": {
            "scenario": network_metrics["network_scenario"],
            "latency_ms": network_metrics["latency_ms"],
            "packet_loss": network_metrics["packet_loss"],
        },
        "event_features": {
            "max_confidence": round(float(row["max_confidence"]), 3),
            "avg_confidence": round(float(row["avg_confidence"]), 3),
            "object_count": round(float(row["object_count"]), 3),
            "fire_smoke_ratio": round(float(row["fire_smoke_ratio"]), 3),
            "bbox_area_ratio": round(float(row["bbox_area_ratio"]), 3),
            "detection_density_5s": round(float(row["detection_density_5s"]), 3),
            "detection_density_10s": round(float(row["detection_density_10s"]), 3),
            "avg_confidence_5s": round(float(row["avg_confidence_5s"]), 3),
            "consecutive_fire_ratio": round(float(row["consecutive_fire_ratio"]), 3),
            "bbox_area_growth": round(float(row["bbox_area_growth"]), 3),
            "brightness": round(float(row["brightness"]), 3),
            "blur_score": round(float(row["blur_score"]), 3),
            "motion_level": round(float(row["motion_level"]), 3),
        },
        "image_sent": True,
        "image_path": image_path,
        "alert_flag": True,
    }


def decide_action(decision):
    """Map ML decision to final transmission action."""
    if decision == "DROP":
        return "LOCAL_ONLY"

    if decision == "SEND_METADATA":
        return "PUBLISH_JSON_METADATA"

    if decision == "SEND_FULL":
        return "PUBLISH_JSON_AND_IMAGE"

    return "UNKNOWN"


def save_payload(payload, event_id):
    """Save JSON payload locally as mock cloud transmission."""
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)

    payload_type = payload["payload_type"].lower()
    payload_path = PAYLOAD_DIR / f"event_{event_id}_{payload_type}.json"

    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)

    return str(payload_path)


def main():
    """Run event-level ML decision, QoS assignment, and mock transmission."""
    df = pd.read_csv(DATASET_PATH)
    engine = MLDecisionEngine()

    logs = []

    for event_id, row in df.iterrows():
        feature_dict = row[FEATURES].to_dict()

        # Predict event-level transmission decision
        decision = engine.predict(feature_dict)

        # Simulate network condition and assign QoS
        network_metrics = simulate_network_metrics()
        qos = assign_qos(decision, network_metrics)

        action = decide_action(decision)

        payload = None
        payload_path = None
        image_path = None
        payload_type = "NONE"

        if decision == "SEND_METADATA":
            payload = build_metadata_payload(
                row=row,
                decision=decision,
                qos=qos,
                network_metrics=network_metrics
            )
            payload_path = save_payload(payload, event_id)
            payload_type = "METADATA_ONLY"

        elif decision == "SEND_FULL":
            # Placeholder until real best-frame selection is connected
            image_path = "representative_frame_placeholder.jpg"

            payload = build_full_payload(
                row=row,
                decision=decision,
                qos=qos,
                network_metrics=network_metrics,
                image_path=image_path
            )
            payload_path = save_payload(payload, event_id)
            payload_type = "FULL_EVENT"

        # DROP creates no cloud payload, only local log
        logs.append({
            "event_id": event_id,
            "video_name": row["video_name"],
            "camera_id": row["camera_name"],
            "window_start_sec": row["window_start_sec"],
            "window_end_sec": row["window_end_sec"],
            "ml_decision": decision,
            "network_scenario": network_metrics["network_scenario"],
            "latency_ms": network_metrics["latency_ms"],
            "packet_loss": network_metrics["packet_loss"],
            "qos": qos,
            "final_action": action,
            "payload_type": payload_type,
            "image_sent": decision == "SEND_FULL",
            "payload_path": payload_path,
            "image_path": image_path,
        })

        print(
            f"Event {event_id}: "
            f"{decision} | "
            f"QoS={qos} | "
            f"Network={network_metrics['network_scenario']} | "
            f"Action={action} | "
            f"Payload={payload_type}"
        )

    log_df = pd.DataFrame(logs)
    log_df.to_csv(LOG_PATH, index=False)

    print("\n✅ Decision pipeline finished")
    print(f"✅ Log saved to: {LOG_PATH}")
    print(f"✅ Payloads saved to: {PAYLOAD_DIR}")

    print("\nDecision distribution:")
    print(log_df["ml_decision"].value_counts())

    print("\nAction distribution:")
    print(log_df["final_action"].value_counts())

    print("\nPayload distribution:")
    print(log_df["payload_type"].value_counts())


if __name__ == "__main__":
    main()