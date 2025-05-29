resource "aws_dynamodb_table" "game_data" {
  name         = "${var.project_name}-data"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "team_id"

  attribute {
    name = "team_id"
    type = "S"
  }
}
