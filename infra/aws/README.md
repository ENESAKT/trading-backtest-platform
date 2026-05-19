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
Ubuntu 24.04 LTS AMI değeri Terraform tarafından AWS'ten otomatik seçilir.
Varsayılan instance tipi hesap vCPU kotası düşük olan yeni AWS hesapları için `t2.small` tutulur; production yük artınca EC2 On-Demand vCPU kotası yükseltilip `t3.large` veya daha büyük tipe geçilmelidir.

## Kullanıcı Aksiyonu Gerektirir

- AWS hesabında eski NAT Gateway, RDS, App Runner, EIP ve EBS maliyetlerinin kontrolü
- `piyasapilot-key` SSH anahtarının güvenli üretilmesi
- METUnic DNS A kayıtlarının Elastic IP'ye yönlendirilmesi
- TLS sertifikasının sunucuda Certbot ile alınması
- S3 yedek bucket ve IAM backup kullanıcısının oluşturulması

## EC2 İlk Açılış Sırası

1. Elastic IP'yi domain A kayıtlarına bağla.
2. Repo'yu `/opt/piyasapilot` altına clone'la.
3. Ek EBS volume'u Docker data-root olarak bağla:
   ```bash
   cd /opt/piyasapilot
   sudo bash scripts/deployment/setup_ec2_data_volume.sh
   ```
4. `.env.production` dosyasını gerçek secret ve domain değerleriyle doldur.
5. İlk kalkışta HTTP bootstrap nginx kullan:
   ```bash
   cd /opt/piyasapilot/infra
   NGINX_CONF=../docker/nginx.bootstrap.conf docker compose --env-file ../.env.production -f docker-compose.prod.yml up -d --build
   ```
6. TLS'i compose mount path'lerine yazdır:
   ```bash
   cd /opt/piyasapilot
   DOMAIN=piyasapilot.com EMAIL=admin@piyasapilot.com bash scripts/deployment/setup_tls.sh
   ```
7. Production TLS nginx'e dön:
   ```bash
   cd /opt/piyasapilot/infra
   docker compose --env-file ../.env.production -f docker-compose.prod.yml up -d nginx
   ```
