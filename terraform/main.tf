########################################
# Terraform AWS starter configuration
########################################

# Random suffix for unique naming
resource "random_id" "suffix" {
  byte_length = 4
}

########################################
# S3 bucket for raw IoT events
########################################

resource "aws_s3_bucket" "iot_raw_events" {
  bucket = "gohar-iot-raw-events-${random_id.suffix.hex}"

  force_destroy = false

  tags = {
    Project = "iot-hybrid"
    Owner   = "Gohar"
    Env     = "dev"
  }
}

########################################
# Enable versioning
########################################

resource "aws_s3_bucket_versioning" "iot_raw_events_versioning" {
  bucket = aws_s3_bucket.iot_raw_events.id

  versioning_configuration {
    status = "Enabled"
  }
}

########################################
# Block public access (security)
########################################

resource "aws_s3_bucket_public_access_block" "iot_raw_events_block_public" {
  bucket                  = aws_s3_bucket.iot_raw_events.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

########################################
# Output bucket name
########################################

output "s3_bucket_name" {
  value       = aws_s3_bucket.iot_raw_events.bucket
  description = "Name of the S3 bucket for raw IoT events"
}
########################################
# AWS IoT Thing
########################################

resource "aws_iot_thing" "fire_detector" {
  name = "fire-detector-device"

  attributes = {
    project = "iot-hybrid"
    owner   = "Gohar"
  }
}
########################################
# IoT Certificate
########################################

resource "aws_iot_certificate" "fire_detector_cert" {
  active = true
}
########################################
# IoT Policy
########################################

resource "aws_iot_policy" "fire_detector_policy" {
  name = "fire-detector-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iot:Connect",
          "iot:Publish",
          "iot:Subscribe",
          "iot:Receive"
        ]
        Resource = "*"
      }
    ]
  })
}
resource "aws_iot_thing_principal_attachment" "attach_cert_to_thing" {
  thing     = aws_iot_thing.fire_detector.name
  principal = aws_iot_certificate.fire_detector_cert.arn
}

resource "aws_iot_policy_attachment" "attach_policy_to_cert" {
  policy = aws_iot_policy.fire_detector_policy.name
  target = aws_iot_certificate.fire_detector_cert.arn
}