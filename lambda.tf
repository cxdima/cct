data "aws_caller_identity" "current" {}

# 1) BOT Dependencies Layer
resource "aws_lambda_layer_version" "telegram_bot_deps" {
  filename            = "telegram_bot_layer.zip"
  layer_name          = "${var.project_name}-telegram-bot-deps"
  compatible_runtimes = ["python3.11"]
}

# 2) BOT Lambda
resource "aws_lambda_function" "bot_handler" {
  function_name    = "${var.project_name}-bot-lambda"
  runtime          = "python3.11"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.bot_lambda_role.arn
  filename         = "bot_lambda_function.zip"
  source_code_hash = filebase64sha256("bot_lambda_function.zip")

  environment {
    variables = {
      TELEGRAM_TOKEN = var.telegram_token
    }
  }

  layers      = [aws_lambda_layer_version.telegram_bot_deps.arn]
  memory_size = 512
  timeout     = 10
}

# 3) BOT Function URL (public, no auth)
resource "aws_lambda_function_url" "bot_url" {
  function_name      = aws_lambda_function.bot_handler.function_name
  authorization_type = "NONE"
}

resource "aws_lambda_permission" "bot_url_invoke" {
  statement_id          = "AllowPublicInvokeBot"
  action                = "lambda:InvokeFunctionUrl"
  function_name         = aws_lambda_function.bot_handler.function_name
  principal             = "*"
  function_url_auth_type = "NONE"
}

# 4) REST Lambda
resource "aws_lambda_function" "rest_handler" {
  function_name    = "${var.project_name}-rest-lambda"
  runtime          = "python3.11"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.rest_lambda_role.arn
  filename         = "rest_lambda_function.zip"
  source_code_hash = filebase64sha256("rest_lambda_function.zip")

  environment {
    variables = {
      TABLE_LOC = aws_dynamodb_table.locations.name
    }
  }
}

# 5) REST Function URL (public, no auth)
resource "aws_lambda_function_url" "rest_url" {
  function_name      = aws_lambda_function.rest_handler.function_name
  authorization_type = "NONE"
}

resource "aws_lambda_permission" "rest_url_invoke" {
  statement_id          = "AllowPublicInvokeRest"
  action                = "lambda:InvokeFunctionUrl"
  function_name         = aws_lambda_function.rest_handler.function_name
  principal             = "*"
  function_url_auth_type = "NONE"
}

# 6) Expose URLs as outputs
output "bot_function_url" {
  description = "Invoke URL for the Telegram-bot Lambda"
  value       = aws_lambda_function_url.bot_url.function_url
}

output "rest_function_url" {
  description = "Invoke URL for the REST Lambda"
  value       = aws_lambda_function_url.rest_url.function_url
}
