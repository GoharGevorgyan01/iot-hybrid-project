output "iot_certificate_pem" {
  value     = aws_iot_certificate.fire_detector_cert.certificate_pem
  sensitive = true
}

output "iot_private_key" {
  value     = aws_iot_certificate.fire_detector_cert.private_key
  sensitive = true
}

output "iot_certificate_arn" {
  value = aws_iot_certificate.fire_detector_cert.arn
}