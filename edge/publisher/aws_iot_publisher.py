import json
import os
from awscrt import mqtt
from awsiot import mqtt_connection_builder

# =========================================
# AWS IoT connection settings
# =========================================
ENDPOINT = "a3qhxuv9z6pj06-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "fire-detector-device"
TOPIC = "fire_smoke/predictions"

# Base directory of project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Certificate file paths
CERT_PATH = os.path.join(BASE_DIR, "edge", "publisher", "certs", "device.pem.crt")
KEY_PATH = os.path.join(BASE_DIR, "edge", "publisher", "certs", "private.pem.key")
ROOT_CA_PATH = os.path.join(BASE_DIR, "edge", "publisher", "certs", "AmazonRootCA1.pem")


def publish_payload(payload):
    print("Connecting to AWS IoT Core...")

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=CERT_PATH,
        pri_key_filepath=KEY_PATH,
        ca_filepath=ROOT_CA_PATH,
        client_id=CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30
    )

    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("Connected.")

    print(f"Publishing to topic: {TOPIC}")
    mqtt_connection.publish(
        topic=TOPIC,
        payload=json.dumps(payload),
        qos=mqtt.QoS.AT_LEAST_ONCE
    )
    print("Message published successfully.")

    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected.")