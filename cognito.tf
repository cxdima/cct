# 1) Cognito User Pool (no MFA, only admin can create users)
resource "aws_cognito_user_pool" "main" {
  name              = "${var.project_name}-user-pool"
  mfa_configuration = "OFF"

  admin_create_user_config {
    allow_admin_create_user_only = true
  }
}

# 2) App Client (no secret, password + SRP flows)
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

# 3) Two Groups: admin & captain
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

# 4) Two Users: admin & captain, with permanent passwords
resource "aws_cognito_user" "admin_user" {
  user_pool_id   = aws_cognito_user_pool.main.id
  username       = "admin"
  password       = "admin"
  message_action = "SUPPRESS"
}

resource "aws_cognito_user" "captain_user" {
  user_pool_id   = aws_cognito_user_pool.main.id
  username       = "captain"
  password       = "captain"
  message_action = "SUPPRESS"
}

# 5) Assign each user to its group
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
