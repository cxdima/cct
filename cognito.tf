resource "aws_cognito_user_pool" "main" {
  name              = "${var.project_name}-user-pool"
  mfa_configuration = "OFF"

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length                   = 6
    require_lowercase                = false
    require_numbers                  = false
    require_symbols                  = false
    require_uppercase                = false
    temporary_password_validity_days = 7
  }
}

resource "aws_cognito_user_pool_client" "web_client" {
  name            = "${var.project_name}-web-client"
  user_pool_id    = aws_cognito_user_pool.main.id
  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
  ]
}

resource "aws_cognito_user_group" "admin_group" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.main.id
  precedence   = 0
}

resource "aws_cognito_user_group" "captain_group" {
  name         = "captain"
  user_pool_id = aws_cognito_user_pool.main.id
  precedence   = 1
}

resource "aws_cognito_user" "admin_user" {
  user_pool_id   = aws_cognito_user_pool.main.id
  username       = "admin"
  password       = "cxdima"
  message_action = "SUPPRESS"
}

resource "aws_cognito_user" "captain_user" {
  user_pool_id   = aws_cognito_user_pool.main.id
  username       = "captain"
  password       = "cxdima"
  message_action = "SUPPRESS"
}

resource "aws_cognito_user_in_group" "admin_membership" {
  user_pool_id = aws_cognito_user_pool.main.id
  username     = aws_cognito_user.admin_user.username
  group_name   = aws_cognito_user_group.admin_group.name
}

resource "aws_cognito_user_in_group" "captain_membership" {
  user_pool_id = aws_cognito_user_pool.main.id
  username     = aws_cognito_user.captain_user.username
  group_name   = aws_cognito_user_group.captain_group.name
}
