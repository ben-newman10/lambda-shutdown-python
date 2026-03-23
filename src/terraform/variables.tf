variable "region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-west-2"
}

variable "tag_key" {
  description = "Tag key to identify EC2 instances to stop"
  type        = string
}

variable "tag_value" {
  description = "Tag value to identify EC2 instances to stop"
  type        = string
}

variable "dlq_message_retention_days" {
  description = "Number of days to retain messages in the Dead Letter Queue"
  type        = number
  default     = 14
}

variable "lambda_timeout_seconds" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_mb" {
  description = "Lambda function memory allocation in MB"
  type        = number
  default     = 256
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 30
}

variable "kms_deletion_window_days" {
  description = "KMS key deletion window in days"
  type        = number
  default     = 7
}
