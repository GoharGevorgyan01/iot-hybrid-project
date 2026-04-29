import mysql.connector

# -----------------------------
# DATABASE CONNECTION SETTINGS
# -----------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "esgogiknem1",
    "database": "fire_smoke_db"
}

# -----------------------------
# DECISION FUNCTION
# -----------------------------
# Input:
# - fire_count, smoke_count: հայտնաբերված fire/smoke օբյեկտների քանակ
# - max_confidence: frame-ի ամենաբարձր confidence-ը
# - latency_ms, packet_loss, bandwidth_usage_kb: network վիճակ
# - motion_level: frame-ի շարժման մակարդակ
# - frame_size_kb: frame-ի չափը
#
# Output:
# - priority_level
# - transmission_action
# - selected_qos
# - destination
# - reason_text
# - alert_flag
def make_decision(
    fire_count,
    smoke_count,
    total_detected_objects,
    max_confidence,
    latency_ms,
    packet_loss,
    bandwidth_usage_kb,
    motion_level,
    frame_size_kb
):
    # 1. Fire with strong confidence -> critical event
    if fire_count > 0 and max_confidence >= 0.70:
        return "high", "send", 2, "cloud", "fire detected with high confidence", 1

    # 2. Multiple fire/smoke detections with decent confidence -> important event
    if total_detected_objects >= 3 and max_confidence >= 0.55:
        return "high", "send", 2, "cloud", "multiple detections in frame", 1

    # 3. Smoke with medium confidence -> medium priority
    if smoke_count > 0 and max_confidence >= 0.50:
        return "medium", "compress", 1, "cloud", "smoke detected", 1

    # 4. High motion + detection -> send compressed
    if (fire_count > 0 or smoke_count > 0) and motion_level >= 0.50:
        return "medium", "compress", 1, "cloud", "event with high motion level", 1

    # 5. Large frame + weak bandwidth -> compress instead of full send
    if (fire_count > 0 or smoke_count > 0) and frame_size_kb >= 120 and bandwidth_usage_kb < 200:
        return "medium", "compress", 1, "cloud", "large frame under limited bandwidth", 1

    # 6. No detection + bad network -> drop
    if fire_count == 0 and smoke_count == 0 and (packet_loss > 5 or latency_ms > 200):
        return "low", "drop", 0, "edge", "no detection and bad network", 0

    # 7. No detection + normal network -> local store only
    if fire_count == 0 and smoke_count == 0:
        return "low", "local_store", 0, "edge", "no critical event", 0

    # 8. Default fallback
    return "low", "local_store", 0, "edge", "default low-priority decision", 0


# -----------------------------
# CONNECT TO MYSQL
# -----------------------------
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

# -----------------------------
# QUERY: COLLECT FRAME SUMMARY
# -----------------------------
query = """
SELECT
    f.frame_id,
    f.file_name,
    f.motion_level,
    f.frame_size_kb,
    SUM(CASE WHEN d.object_type = 'smoke' THEN 1 ELSE 0 END) AS smoke_count,
    SUM(CASE WHEN d.object_type = 'fire' THEN 1 ELSE 0 END) AS fire_count,
    COUNT(d.detection_id) AS total_detected_objects,
    MAX(d.confidence) AS max_confidence,
    nm.latency_ms,
    nm.packet_loss,
    nm.bandwidth_usage_kb
FROM frames f
LEFT JOIN detections d ON f.frame_id = d.frame_id
LEFT JOIN network_metrics nm ON f.frame_id = nm.frame_id
GROUP BY
    f.frame_id,
    f.file_name,
    f.motion_level,
    f.frame_size_kb,
    nm.latency_ms,
    nm.packet_loss,
    nm.bandwidth_usage_kb
"""

cursor.execute(query)
rows = cursor.fetchall()

inserted_decisions = 0
inserted_alerts = 0

# optional: clear previous alerts to avoid duplicates for rerun
cursor.execute("DELETE FROM alerts")

for row in rows:
    frame_id = row["frame_id"]
    fire_count = row["fire_count"] or 0
    smoke_count = row["smoke_count"] or 0
    total_detected_objects = row["total_detected_objects"] or 0
    max_confidence = row["max_confidence"] or 0.0
    latency_ms = row["latency_ms"] or 0.0
    packet_loss = row["packet_loss"] or 0.0
    bandwidth_usage_kb = row["bandwidth_usage_kb"] or 0.0
    motion_level = row["motion_level"] or 0.0
    frame_size_kb = row["frame_size_kb"] or 0.0

    priority_level, transmission_action, selected_qos, destination, reason_text, alert_flag = make_decision(
        fire_count,
        smoke_count,
        total_detected_objects,
        max_confidence,
        latency_ms,
        packet_loss,
        bandwidth_usage_kb,
        motion_level,
        frame_size_kb
    )

    # remove old decision for same frame
    cursor.execute("DELETE FROM transmission_decisions WHERE frame_id = %s", (frame_id,))

    # insert new decision
    cursor.execute("""
        INSERT INTO transmission_decisions
        (frame_id, priority_level, transmission_action, selected_qos, destination, reason_text, alert_flag)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        frame_id,
        priority_level,
        transmission_action,
        selected_qos,
        destination,
        reason_text,
        alert_flag
    ))
    inserted_decisions += 1

    # create alert only for medium/high important events
    if alert_flag == 1:
        cursor.execute("""
            INSERT INTO alerts
            (frame_id, alert_type, alert_message, severity, sent_to, alert_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            frame_id,
            "detection_alert",
            reason_text,
            priority_level,
            "local_system",
            "created"
        ))
        inserted_alerts += 1

conn.commit()
cursor.close()
conn.close()

print(f"Done. Inserted {inserted_decisions} decisions and {inserted_alerts} alerts.")