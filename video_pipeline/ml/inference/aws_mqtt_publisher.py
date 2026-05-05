import ssl
import json
import paho.mqtt.client as mqtt

from video_pipeline.ml.inference.aws_config import (
    AWS_IOT_ENDPOINT,
    ROOT_CA_PATH,
    CERT_PATH,
    PRIVATE_KEY_PATH,
    MQTT_TOPIC_METADATA,
    MQTT_TOPIC_FULL,
)


class AWSIoTPublisher:
    def __init__(self):
        self.client = mqtt.Client()

        self.client.tls_set(
            ca_certs=ROOT_CA_PATH,
            certfile=CERT_PATH,
            keyfile=PRIVATE_KEY_PATH,
            tls_version=ssl.PROTOCOL_TLSv1_2,
        )

        self.client.connect(AWS_IOT_ENDPOINT, 8883)
        self.client.loop_start()

    def publish(self, payload: dict, qos: int):
        payload_type = payload.get("payload_type")

        if payload_type == "FULL_EVENT":
            topic = MQTT_TOPIC_FULL
        else:
            topic = MQTT_TOPIC_METADATA

        message = json.dumps(payload)

        result = self.client.publish(topic, message, qos=qos)
       

        print(f"[MQTT] Published to {topic} | QoS={qos} | rc={result.rc}")
        print(f"[MQTT] Payload: {message[:100]}...\n")

        return result

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("[MQTT] Connection closed")