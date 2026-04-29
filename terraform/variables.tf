variable "aws_region" {
  description = "AWS region used for IoT Core and S3"
  type        = string
  default     = "eu-central-1"
}

variable "s3_bucket_name" {
  description = "Existing S3 bucket name used by the IoT video pipeline"
  type        = string
}

variable "iot_topic_name" {
  description = "MQTT topic used by the Python pipeline for event JSON messages"
  type        = string
  default     = "iot/video/full"
}

variable "json_prefix" {
  description = "S3 prefix where IoT JSON payloads will be stored"
  type        = string
  default     = "json-events/"
}