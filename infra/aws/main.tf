terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_key_pair" "piyasapilot" {
  key_name   = "piyasapilot-key"
  public_key = file(var.public_key_path)
}

resource "aws_security_group" "piyasapilot" {
  name        = "piyasapilot-sg"
  description = "PiyasaPilot production web ingress"

  ingress {
    description = "SSH from operator IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  ingress {
    description = "HTTP for certbot and redirect"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS public traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "piyasapilot" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.piyasapilot.key_name
  vpc_security_group_ids = [aws_security_group.piyasapilot.id]

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
  }

  tags = {
    Name    = "piyasapilot-prod"
    Project = "PiyasaPilot"
  }
}

resource "aws_ebs_volume" "data" {
  availability_zone = aws_instance.piyasapilot.availability_zone
  size              = 100
  type              = "gp3"

  tags = {
    Name    = "piyasapilot-data"
    Project = "PiyasaPilot"
  }
}

resource "aws_volume_attachment" "data" {
  device_name = "/dev/sdb"
  volume_id   = aws_ebs_volume.data.id
  instance_id = aws_instance.piyasapilot.id
}

resource "aws_eip" "piyasapilot" {
  instance = aws_instance.piyasapilot.id
  domain   = "vpc"

  tags = {
    Name    = "piyasapilot-eip"
    Project = "PiyasaPilot"
  }
}

output "elastic_ip" {
  value = aws_eip.piyasapilot.public_ip
}
