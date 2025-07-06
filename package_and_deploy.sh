#!/usr/bin/env bash
set -euo pipefail

# 1) Package the REST lambda (everything under rest_lambda/)
echo "Packaging rest_lambda…"
(
  cd rest_lambda
  zip -r ../rest_lambda_function.zip .
)

# 2) Package the Bot lambda (everything under bot_lambda/)
echo "Packaging bot_lambda…"
(
  cd bot_lambda
  zip -r ../bot_lambda_function.zip .
)

# 3) Initialize & apply Terraform
echo "Initializing Terraform…"
terraform init -input=false

echo "Planning & applying Terraform…"
terraform apply -auto-approve
