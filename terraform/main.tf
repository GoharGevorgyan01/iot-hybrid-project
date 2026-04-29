terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS provider configuration
provider "aws" {
  region = var.aws_region
}

# Existing S3 bucket ARN.
# We do not read or create the bucket here.
# The bucket name is passed through terraform.tfvars.
locals {
  s3_bucket_arn = "arn:aws:s3:::${var.s3_bucket_name}"
}

# IAM role that allows AWS IoT Core to write JSON payloads into S3
resource "aws_iam_role" "iot_s3_rule_role" {
  name = "iot-video-pipeline-iot-s3-rule-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "iot.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# IAM policy that gives IoT Core permission to put JSON objects into S3
resource "aws_iam_role_policy" "iot_s3_put_policy" {
  name = "iot-video-pipeline-s3-put-policy"
  role = aws_iam_role.iot_s3_rule_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${local.s3_bucket_arn}/${var.json_prefix}*"
      }
    ]
  })
}

# IoT Rule:
# It listens to the MQTT topic and stores incoming JSON messages into S3.
resource "aws_iot_topic_rule" "save_events_to_s3" {
  name        = "iot_video_pipeline_save_events_to_s3"
  description = "Save IoT video pipeline MQTT JSON events to S3"
  enabled     = true

  sql         = "SELECT * FROM '${var.iot_topic_name}'"
  sql_version = "2016-03-23"

  s3 {
    bucket_name = var.s3_bucket_name

    # AWS IoT evaluates timestamp() at runtime.
    key = "${var.json_prefix}${timestamp()}.json"

    role_arn = aws_iam_role.iot_s3_rule_role.arn
  }
}