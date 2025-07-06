# Chakra CCT

This repository contains the infrastructure and Lambda code for the **Chakra CCT** project. The game is developed for the Twitch streamer **ChakraLounge** and is inspired by classic mafia style table games. Team captains interact with the game through a Telegram bot while the backend runs entirely on AWS.

## Repository layout

- `bot_lambda/` – Telegram bot handler written in Python. This Lambda function receives updates from Telegram and controls most game mechanics.
- `rest_lambda/` – Simple REST API endpoints used by the web client.
- `package/` and `telegram_bot_layer.zip` – Python dependencies bundled as a Lambda layer for the bot.
- `*.tf` – Terraform configuration for DynamoDB tables, IAM roles, S3 bucket and Lambda functions.
- `package_and_deploy.sh` – Helper script that zips the Lambda sources and applies the Terraform plan.

## Telegram bot

The bot exposes the following commands:

- `/start` – shows the main menu if the user is authorised.
- `/init <team_id>` – links a Telegram group with a team in the database.

The bot allows team captains to buy or use items, view members, open locations and check the leaderboard. All state is stored in the DynamoDB table `cct-telegram-users`.

## Deployment

1. Install [Terraform](https://www.terraform.io/) and configure your AWS credentials.
2. Set the `TELEGRAM_TOKEN` variable (either export it in the environment or supply it through Terraform variables).
3. Run `./package_and_deploy.sh` to zip the Lambda functions and deploy the infrastructure.

The script performs the following steps:

```bash
./package_and_deploy.sh
```

This creates/updates the Lambda functions, the DynamoDB tables and the S3 bucket defined in the Terraform files. After the apply step it outputs the Function URLs for both the bot and the REST API.

## Hosting

The REST Lambda and Telegram bot are deployed as public Lambda function URLs. A static website bucket is also created (see `s3.tf`) which can be used to serve a client for the game.

## Development notes

- Python 3.11 is used for the Lambda runtimes.
- Dependencies for the bot are prepackaged in `telegram_bot_layer.zip` to keep deployment size small.
- The repository currently contains minimal game logic and is intended as a starting point for further development.

## License

This project is provided as-is for ChakraLounge and currently has no explicit license.
