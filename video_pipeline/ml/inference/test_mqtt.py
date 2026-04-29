import time
from aws_mqtt_publisher import AWSIoTPublisher

publisher = AWSIoTPublisher()

test_payload = {
    "payload_type": "METADATA_ONLY",
    "camera_id": "cam01",
    "ml_decision": "SEND_METADATA",
    "qos": 1,
    "event_features": {
        "max_confidence": 0.82,
        "object_count": 5
    }
}

publisher.publish(test_payload, qos=1)

time.sleep(3)