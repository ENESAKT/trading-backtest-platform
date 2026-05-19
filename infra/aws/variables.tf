variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "instance_type" {
  type    = string
  default = "t2.small"
}

variable "ssh_cidr" {
  type        = string
  description = "Operator public IP in CIDR form, for example 203.0.113.10/32."
}

variable "public_key_path" {
  type        = string
  description = "Path to the SSH public key used for EC2 access."
}
