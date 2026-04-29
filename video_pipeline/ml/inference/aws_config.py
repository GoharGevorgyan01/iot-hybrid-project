AWS_IOT_ENDPOINT = "a3qhxuv9z6pj06-ats.iot.us-east-1.amazonaws.com"

ROOT_CA_PATH = "edge/publisher/certs/AmazonRootCA1.pem"
CERT_PATH = "edge/publisher/certs/device.pem.crt"
PRIVATE_KEY_PATH = "edge/publisher/certs/private.pem.key"

MQTT_TOPIC_METADATA = "iot/video/metadata"
MQTT_TOPIC_FULL = "iot/video/full"

S3_BUCKET_NAME = "iot-video-pipeline-events"

S3_IMAGE_PREFIX = "images/"
S3_JSON_PREFIX = "json/"