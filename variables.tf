variable "project_name" {
  default = "rtsgame"
}

variable "aws_region" {
  default = "us-east-1"
}

variable "telegram_token" {
  description = "Telegram bot token"
  type        = string
  sensitive   = true
}
