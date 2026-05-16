# AWS Deployment Scaffold

Bu klasör canlı AWS kaynağı oluşturmaz; production kurulumu için güvenli Terraform başlangıcı ve manuel kontrol listesi sağlar.

## Kullanım

```bash
cd infra/aws
terraform init
terraform plan \
  -var="ssh_cidr=<SENIN_IPIN>/32" \
  -var="public_key_path=$HOME/.ssh/piyasapilot-key.pub"
```

`terraform apply` yalnızca AWS hesap, bütçe alarmı, IAM ve domain/TLS kararları netleştikten sonra çalıştırılmalı.

## Kullanıcı Aksiyonu Gerektirir

- AWS hesabında eski NAT Gateway, RDS, App Runner, EIP ve EBS maliyetlerinin kontrolü
- `piyasapilot-key` SSH anahtarının güvenli üretilmesi
- METUnic DNS A kayıtlarının Elastic IP'ye yönlendirilmesi
- TLS sertifikasının sunucuda Certbot ile alınması
- S3 yedek bucket ve IAM backup kullanıcısının oluşturulması
