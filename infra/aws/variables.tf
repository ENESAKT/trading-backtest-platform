variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "ami_id" {
  type        = string
  description = "Ubuntu 24.04 LTS AMI id for eu-central-1. Verify in AWS console before apply."
}

variable "instance_type" {
  type    = string
  default = "t3.large"
}

variable "ssh_cidr" {
  type        = string
  description = "Operator public IP in CIDR form, for example 203.0.113.10/32."
}

variable "public_key_path" {
  type        = string
  description = "Path to the SSH public key used for EC2 access."
}
