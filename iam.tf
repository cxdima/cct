#------------------------------------------------------------
# 1) BOT Lambda Role (basic execution + read-only DynamoDB)
#------------------------------------------------------------
resource "aws_iam_role" "bot_lambda_role" {
  name = "${var.project_name}-bot-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# Basic logging/execution
resource "aws_iam_role_policy_attachment" "bot_basic_execution" {
  role       = aws_iam_role.bot_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Read-only DDB policy for bot
resource "aws_iam_policy" "bot_dynamodb_read" {
  name        = "${var.project_name}-bot-dynamodb-read"
  description = "Allow bot-lambda read access to cct-telegram-users table"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "dynamodb:GetItem",
          "dynamodb:BatchGetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.telegram_users.arn
        ]
      }
    ]
  })
}

# Attach the read-only policy to bot role
resource "aws_iam_role_policy_attachment" "bot_dynamodb_read_attach" {
  role       = aws_iam_role.bot_lambda_role.name
  policy_arn = aws_iam_policy.bot_dynamodb_read.arn
}

#------------------------------------------------------------
# 2) REST Lambda Role (basic execution + locked-down DynamoDB)
#------------------------------------------------------------
resource "aws_iam_role" "rest_lambda_role" {
  name = "${var.project_name}-rest-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# REST basic execution
resource "aws_iam_role_policy_attachment" "rest_basic_execution" {
  role       = aws_iam_role.rest_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# REST read/write policy for three tables
resource "aws_iam_policy" "rest_dynamodb_policy" {
  name        = "${var.project_name}-rest-dynamodb-policy"
  description = "Allow rest-lambda full access to three DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "dynamodb:GetItem",
          "dynamodb:BatchGetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = [
          aws_dynamodb_table.locations.arn,
          aws_dynamodb_table.telegram_users.arn,
          aws_dynamodb_table.game_data.arn
        ]
      }
    ]
  })
}

# Attach the REST DynamoDB policy
resource "aws_iam_policy_attachment" "rest_dynamodb_attach" {
  name       = "${var.project_name}-rest-dynamodb-attach"
  roles      = [aws_iam_role.rest_lambda_role.name]
  policy_arn = aws_iam_policy.rest_dynamodb_policy.arn
}
