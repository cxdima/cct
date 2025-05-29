resource "aws_instance" "telegram_bot" {
  ami           = "ami-0c101f26f147fa7fd" # Amazon Linux 2023 (HVM)
  instance_type = "t3.micro"
  key_name      = "chakra-cct"

  tags = {
    Name = "${var.project_name}-telegram-bot"
  }

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y python3 git
              cd /home/ec2-user
              git clone https://git-codecommit.us-east-1.amazonaws.com/v1/repos/${var.project_name}-repo
              cd ${var.project_name}-repo
              pip3 install -r requirements.txt
              python3 bot.py &
              EOF

  iam_instance_profile = aws_iam_instance_profile.ec2_instance_profile.name
}
