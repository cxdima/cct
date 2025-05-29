resource "aws_codecommit_repository" "repo" {
  repository_name = "${var.project_name}-repo"
  description     = "Repo for RTS Game Telegram bot"
}

resource "aws_codebuild_project" "build" {
  name         = "${var.project_name}-build"
  service_role = aws_iam_role.codebuild_role.arn
  source {
    type     = "CODECOMMIT"
    location = aws_codecommit_repository.repo.clone_url_http
    buildspec = file("buildspec.yml")
  }

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type    = "BUILD_GENERAL1_SMALL"
    image           = "aws/codebuild/standard:6.0"
    type            = "LINUX_CONTAINER"
    privileged_mode = true
  }

}

resource "aws_codedeploy_app" "app" {
  name             = "${var.project_name}-codedeploy"
  compute_platform = "Server"
}

resource "aws_codedeploy_deployment_group" "dg" {
  app_name              = aws_codedeploy_app.app.name
  deployment_group_name = "${var.project_name}-dg"
  service_role_arn      = aws_iam_role.codedeploy_role.arn

  deployment_style {
    deployment_option = "WITHOUT_TRAFFIC_CONTROL"
    deployment_type   = "IN_PLACE"
  }

  ec2_tag_set {
    ec2_tag_filter {
      key   = "Name"
      type  = "KEY_AND_VALUE"
      value = "${var.project_name}-telegram-bot"
    }
  }
}
