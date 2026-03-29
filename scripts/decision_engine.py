import mysql.connector

# -----------------------------
# DATABASE CONNECTION SETTINGS
# -----------------------------
# Այստեղ գրում ենք MySQL-ի connection տվյալները
DB_CONFIG = {
    "host": "localhost",          # MySQL server-ը լոկալ համակարգչի վրա է
    "user": "root",               # MySQL username
    "password": "esgogiknem1",    # քո MySQL password-ը
    "database": "fire_smoke_db"   # այն database-ը, որի հետ աշխատում ենք
}

# -----------------------------
# DECISION FUNCTION
# -----------------------------
# Այս function-ը frame-ի detection + network տվյալների հիման վրա
# որոշում է ինչ priority, action, qos և destination պետք է տալ
def make_decision(fire_count, smoke_count, max_confidence, latency_ms, packet_loss, bandwidth_usage_kb):

    # Եթե fire կա և confidence-ը բարձր է
    # նշանակում է դեպքը վտանգավոր է
    # պետք է արագ ու վստահ ուղարկել cloud
    if fire_count > 0 and max_confidence >= 0.70:
        return "high", "send", 2, "cloud", "fire detected with high confidence", 1

    # Եթե fire չկա, բայց smoke կա և confidence-ը միջինից բարձր է
    # սա միջին վտանգավոր դեպք է
    # կարող ենք compress արած ուղարկել cloud
    if smoke_count > 0 and max_confidence >= 0.50:
        return "medium", "compress", 1, "cloud", "smoke detected", 1

    # Եթե fire էլ չկա, smoke էլ չկա, և network-ը վատ է
    # ապա frame-ը իմաստ չունի ուղարկել
    # կարելի է drop անել
    if fire_count == 0 and smoke_count == 0 and (packet_loss > 5 or latency_ms > 200):
        return "low", "drop", 0, "edge", "no detection and bad network", 0

    # Մնացած բոլոր դեպքերում
    # պահում ենք local-ում որպես low-priority data
    return "low", "local_store", 0, "edge", "no critical event", 0


# -----------------------------
# CONNECT TO MYSQL
# -----------------------------
# Բացում ենք կապ database-ի հետ
conn = mysql.connector.connect(**DB_CONFIG)

# dictionary=True նշանակում է, որ row-երը կգան dictionary ձևով
# օրինակ row["frame_id"], row["fire_count"]
cursor = conn.cursor(dictionary=True)

# -----------------------------
# MAIN QUERY
# -----------------------------
# Այս query-ն մեկ frame-ի համար հավաքում է.
# - smoke_count
# - fire_count
# - total detections
# - max_confidence
# - network տվյալներ
query = """
SELECT
    f.frame_id,
    f.file_name,
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
    f.frame_id, f.file_name, nm.latency_ms, nm.packet_loss, nm.bandwidth_usage_kb
"""

# query-ն աշխատացնում ենք
cursor.execute(query)

# վերցնում ենք բոլոր արդյունքները
rows = cursor.fetchall()

# հաշվիչներ, որ վերջում տպենք քանի decision և քանի alert գրանցվեց
inserted_decisions = 0
inserted_alerts = 0

# -----------------------------
# PROCESS EACH FRAME
# -----------------------------
# rows-ի ամեն տողը մեկ frame-ի summary-ն է
for row in rows:
    frame_id = row["frame_id"]

    # եթե SQL aggregate result-ը NULL է, դարձնում ենք 0
    fire_count = row["fire_count"] or 0
    smoke_count = row["smoke_count"] or 0
    max_confidence = row["max_confidence"] or 0.0
    latency_ms = row["latency_ms"] or 0.0
    packet_loss = row["packet_loss"] or 0.0
    bandwidth_usage_kb = row["bandwidth_usage_kb"] or 0.0

    # make_decision function-ը վերադարձնում է որոշման արդյունքները
    priority_level, transmission_action, selected_qos, destination, reason_text, alert_flag = make_decision(
        fire_count, smoke_count, max_confidence, latency_ms, packet_loss, bandwidth_usage_kb
    )

    # Եթե նույն frame-ի համար արդեն decision կար,
    # ջնջում ենք, որ duplicate չլինի
    cursor.execute("DELETE FROM transmission_decisions WHERE frame_id = %s", (frame_id,))

    # Նոր decision-ը գրում ենք transmission_decisions table-ում
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

    # Եթե alert_flag = 1, նշանակում է պետք է նաև alerts table-ում գրանցենք alert
    if alert_flag == 1:
        cursor.execute("""
            INSERT INTO alerts
            (frame_id, alert_type, alert_message, severity, sent_to, alert_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            frame_id,           # որ frame-ի համար է alert-ը
            "detection_alert",  # alert-ի տիպը
            reason_text,        # alert-ի հաղորդագրությունը
            priority_level,     # severity = priority level
            "local_system",     # ում է ուղղված կամ որտեղ է գրանցվել
            "created"           # alert-ի current status
        ))
        inserted_alerts += 1

# database փոփոխությունները վերջնական պահպանում ենք
conn.commit()

# փակում ենք cursor-ը և connection-ը
cursor.close()
conn.close()

# տպում ենք summary
print(f"Done. Inserted {inserted_decisions} decisions and {inserted_alerts} alerts.")