resource "aws_dynamodb_table" "game_data" {
  name         = "${var.project_name}-data"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "team_id"

  attribute {
    name = "team_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "telegram_users" {
  name         = "cct-telegram-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "N"
  }

  attribute {
    name = "team_id"
    type = "N"
  }

  global_secondary_index {
    name               = "team_id-index"
    hash_key           = "team_id"
    projection_type    = "ALL"
  }
}


resource "aws_dynamodb_table" "locations" {
  name         = "locations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "N"
  }

  tags = {
    Environment = "dev"
    Name        = "locations"
  }
}
