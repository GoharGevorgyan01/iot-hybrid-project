import random
import mysql.connector

# ======================
# MYSQL CONNECTION
# ======================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="esgogiknem1",
    database="fire_smoke_db"
)

cursor = conn.cursor(dictionary=True)

# ======================
# CLEAN OLD NETWORK METRICS
# ======================

print("Deleting old rows from network_metrics table...")
cursor.execute("DELETE FROM network_metrics")
cursor.execute("ALTER TABLE network_metrics AUTO_INCREMENT = 1")
conn.commit()
print("Old network metrics deleted and AUTO_INCREMENT reset.")

# ======================
# FETCH FRAME DATA
# ======================

cursor.execute("""
    SELECT frame_id, frame_size_kb, dataset_split
    FROM frames
""")

frames = cursor.fetchall()
print(f"Found {len(frames)} frames.")

# ======================
# INSERT NETWORK METRICS
# ======================

insert_sql = """
INSERT INTO network_metrics
(frame_id, latency_ms, packet_loss, bandwidth_usage_kb, qos_level)
VALUES (%s, %s, %s, %s, %s)
"""

insert_count = 0

for frame in frames:
    frame_id = frame["frame_id"]
    frame_size_kb = frame["frame_size_kb"]
    dataset_split = frame["dataset_split"]

    # Simulated latency depending slightly on split
    if dataset_split == "train":
        latency_ms = round(random.uniform(20, 150), 2)
    elif dataset_split == "val":
        latency_ms = round(random.uniform(30, 200), 2)
    else:  # test
        latency_ms = round(random.uniform(40, 250), 2)

    # Simulated packet loss
    packet_loss = round(random.uniform(0, 15), 2)

    # Simulated bandwidth usage based on frame size
    bandwidth_usage_kb = round(frame_size_kb * random.uniform(0.8, 1.2), 2)

    # Rule-based QoS selection
    if packet_loss > 10:
        qos_level = 2
    elif packet_loss > 5:
        qos_level = 1
    else:
        qos_level = 0

    cursor.execute(
        insert_sql,
        (frame_id, latency_ms, packet_loss, bandwidth_usage_kb, qos_level)
    )

    insert_count += 1

conn.commit()
conn.close()

print(f"Inserted {insert_count} rows into network_metrics successfully.")