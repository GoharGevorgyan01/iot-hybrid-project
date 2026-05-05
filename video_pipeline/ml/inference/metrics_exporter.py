from prometheus_client import Counter, start_http_server


# -----------------------------
# YOLO / frame-level metrics
# -----------------------------

frames_total = Counter(
    "frames_total",
    "Total number of video frames processed by YOLO"
)

frames_with_detection_total = Counter(
    "frames_with_detection_total",
    "Total number of frames where fire/smoke was detected"
)


# -----------------------------
# ML / event-level metrics
# -----------------------------

processed_events_total = Counter(
    "processed_events_total",
    "Total number of processed event-level windows"
)

decision_total = Counter(
    "decision_total",
    "Total number of events by ML decision",
    ["decision"]
)

qos_total = Counter(
    "qos_total",
    "Total number of events by QoS level",
    ["qos"]
)

cloud_action_total = Counter(
    "cloud_action_total",
    "Total number of executed cloud/local actions",
    ["action"]
)

mqtt_publish_total = Counter(
    "mqtt_publish_total",
    "Total number of MQTT publish attempts"
)

s3_upload_total = Counter(
    "s3_upload_total",
    "Total number of successful S3 image uploads"
)

telegram_alert_total = Counter(
    "telegram_alert_total",
    "Total number of Telegram alerts sent"
)


def start_metrics_server(port=8000):
    """Start Prometheus metrics endpoint."""
    start_http_server(port)
    print(f"[Metrics] Prometheus endpoint started on port {port}")


# -----------------------------
# YOLO metric helpers
# -----------------------------

def record_frame_processed():
    """Record one processed video frame."""
    frames_total.inc()


def record_frame_with_detection():
    """Record one frame with fire/smoke detection."""
    frames_with_detection_total.inc()


# -----------------------------
# ML metric helpers
# -----------------------------

def record_event(decision, qos, action):
    """Record one processed event."""
    processed_events_total.inc()
    decision_total.labels(decision=decision).inc()
    qos_total.labels(qos=str(qos)).inc()
    cloud_action_total.labels(action=action).inc()


def record_mqtt_publish():
    """Record MQTT publish."""
    mqtt_publish_total.inc()


def record_s3_upload():
    """Record successful S3 upload."""
    s3_upload_total.inc()


def record_telegram_alert():
    """Record successful Telegram alert."""
    telegram_alert_total.inc()