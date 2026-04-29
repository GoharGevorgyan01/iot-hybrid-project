import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

from s3_uploader import upload_image_to_s3, generate_presigned_url
from aws_mqtt_publisher import AWSIoTPublisher
from inference_engine import MLDecisionEngine
from network_policy import simulate_network_metrics, assign_qos
from telegram_alert import send_critical_alert


BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / "video_pipeline" / ".env")

DATASET_PATH = BASE_DIR / "video_pipeline" / "ml" / "training" / "event_dataset_raw.csv"
LOG_PATH = BASE_DIR / "video_pipeline" / "ml" / "inference" / "decision_log.csv"
PAYLOAD_DIR = BASE_DIR / "video_pipeline" / "ml" / "inference" / "payloads"


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

def build_full_payload(row, decision, qos, network_metrics, image_path, s3_image_key, image_url=None):
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
                "image_sent": s3_image_key is not None,
        "image_path": image_path,
        "s3_image_key": s3_image_key,
        "s3_image_url": image_url,
        "alert_flag": True,
    }


def build_full_payload(row, decision, qos, network_metrics, image_path, s3_image_key, image_url=None):
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
        "s3_image_key": s3_image_key,
        "s3_image_url": image_url,
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
    """Save JSON payload locally for audit/debug."""
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)

    payload_type = payload["payload_type"].lower()
    payload_path = PAYLOAD_DIR / f"event_{event_id}_{payload_type}.json"

    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)

    return str(payload_path)
def get_representative_image_path(row):
    """Return representative image path if the dataset contains one."""

    candidate_columns = [
        "representative_frame_path",
        "frame_path",
        "image_path",
        "file_path",
    ]

    for column in candidate_columns:
        if column in row.index and pd.notna(row[column]):
            return row[column]

    return None

def main():
    """Run ML decision, QoS assignment, local payload save, and MQTT publish."""
    df = pd.read_csv(DATASET_PATH)
    # df = df.head(10)
    
    # Test mode: uncomment this line if full run is slow
    # df = df.head(10)

    engine = MLDecisionEngine()
    publisher = AWSIoTPublisher()

    logs = []
    last_alert_by_camera = {}
    ALERT_COOLDOWN_EVENTS = 5

    try:
        for event_id, row in df.iterrows():
            feature_dict = row[FEATURES].to_dict()

            decision = engine.predict(feature_dict)

            network_metrics = simulate_network_metrics()
            qos = assign_qos(decision, network_metrics)

            # Temporary test fix: avoid QoS 0 message loss in AWS test client
            publish_qos = max(qos, 1)

            action = decide_action(decision)

            payload_path = None
            image_path = None
            s3_image_key = None
            image_url = None
            payload_type = "NONE"
            mqtt_published = False
            telegram_sent = False

            if decision == "SEND_METADATA":
                payload = build_metadata_payload(
                    row=row,
                    decision=decision,
                    qos=publish_qos,
                    network_metrics=network_metrics,
                )

                payload_path = save_payload(payload, event_id)
                publisher.publish(payload, publish_qos)

                payload_type = "METADATA_ONLY"
                mqtt_published = True

            elif decision == "SEND_FULL":
                image_path = get_representative_image_path(row)

                if image_path:
                    s3_image_key = upload_image_to_s3(
                        image_path=image_path,
                        event_id=event_id,
                        camera_id=row["camera_name"],
                    )

                    image_url = generate_presigned_url(s3_image_key)
                else:
                    print(f"[S3] No representative image path for event {event_id}")
                    s3_image_key = None
                    image_url = None

                payload = build_full_payload(
                    row=row,
                    decision=decision,
                    qos=publish_qos,
                    network_metrics=network_metrics,
                    image_path=image_path,
                    s3_image_key=s3_image_key,
                    image_url=image_url,
                )

                payload_path = save_payload(payload, event_id)
                publisher.publish(payload, publish_qos)

                event_data = {
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "camera_id": row["camera_name"],
                    "type": "FIRE/SMOKE",
                    "confidence": round(float(row["max_confidence"]), 3),
                    "risk_score": round(float(row["max_confidence"]), 3),
                    "consecutive_frames": round(float(row["consecutive_fire_ratio"]), 3),
                    "decision": decision,
                    "qos": publish_qos,
                    "event_id": f"evt_{event_id}",
                }

                camera_id = row["camera_name"]
                last_alert_event_id = last_alert_by_camera.get(camera_id)

                should_send_telegram = (
                    last_alert_event_id is None
                    or event_id - last_alert_event_id >= ALERT_COOLDOWN_EVENTS
                )

                if should_send_telegram:
                    telegram_sent = send_critical_alert(
                        event_data=event_data,
                        s3_image_key=s3_image_key,
                        image_url=image_url,
                    )
                    last_alert_by_camera[camera_id] = event_id
                else:
                    print(
                        f"[Telegram] Skipped alert for {camera_id}: "
                        f"cooldown active since event {last_alert_event_id}"
                    )

                payload_type = "FULL_EVENT"
                mqtt_published = True

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
                "publish_qos": publish_qos,
                "final_action": action,
                "payload_type": payload_type,
                "mqtt_published": mqtt_published,
                "telegram_sent": telegram_sent if decision == "SEND_FULL" else False,
                "image_sent": decision == "SEND_FULL",
                "payload_path": payload_path,
                "image_path": image_path,
                "s3_image_key": s3_image_key,
                "s3_image_url": image_url,
            })

            print(
                f"Event {event_id}: "
                f"{decision} | "
                f"QoS={qos} | "
                f"PublishQoS={publish_qos} | "
                f"Network={network_metrics['network_scenario']} | "
                f"Action={action} | "
                f"Payload={payload_type} | "
                f"MQTT={mqtt_published}"
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

    finally:
        import time
        time.sleep(3)
        publisher.close()
if __name__ == "__main__":
    main()