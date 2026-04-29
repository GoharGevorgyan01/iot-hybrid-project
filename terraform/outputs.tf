output "s3_bucket_name" {
  description = "Existing S3 bucket used for event JSON storage"
  value       = var.s3_bucket_name
}

output "iot_topic_name" {
  description = "MQTT topic listened to by the IoT Rule"
  value       = var.iot_topic_name
}

output "iot_rule_name" {
  description = "AWS IoT Rule name"
  value       = aws_iot_topic_rule.save_events_to_s3.name
}

output "iot_s3_role_arn" {
  description = "IAM role ARN used by AWS IoT Rule"
  value       = aws_iam_role.iot_s3_rule_role.arn
}