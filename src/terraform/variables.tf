variable "region" {
  type        = string
  description = "The AWS region where your Lambda function is running"
}

variable "tag_key" {
  type        = string
  description = "The key of the tag to target EC2 instances."
  default     = "Rowden"  # default value
}

variable "tag_value" {
  type        = string
  description = "The value of the tag to target EC2 instances."
  default     = "rowden-example"  # default value
}