# PiyasaPilot Operations Runbook

## Deployment
To deploy a new version to the production server:
1. Ensure your changes are merged to the `main` branch.
2. The GitHub Actions CI/CD pipeline will automatically run tests and deploy to the EC2 instance.
3. To manually deploy from the EC2 server:
   ```bash
   cd /opt/piyasapilot
   git pull origin main
   docker compose -f docker/docker-compose.prod.yml pull
   docker compose -f docker/docker-compose.prod.yml up -d --build
   ```

## Rollback
If a deployment fails or introduces a critical bug:
1. Revert the commit in Git and push to `main` (this triggers a new deployment).
2. Or manually on the server (if using tagged images or git hashes):
   ```bash
   cd /opt/piyasapilot
   git checkout <previous_stable_commit_hash>
   docker compose -f docker/docker-compose.prod.yml up -d --build
   ```

## Restore from Backup
To restore databases from a backup:
1. Ensure `scripts/restore_test.sh` works.
2. Download the desired backup from S3:
   ```bash
   aws s3 cp s3://piyasapilot-backups/daily/backup_YYYYMMDD.tar.gz /tmp/backup.tar.gz
   ```
3. Stop the application services:
   ```bash
   docker compose -f docker/docker-compose.prod.yml down
   ```
4. Extract the backup over the existing data directory (be careful to backup current state first):
   ```bash
   tar -xzf /tmp/backup.tar.gz -C /opt/piyasapilot/data
   ```
5. Restart the application:
   ```bash
   docker compose -f docker/docker-compose.prod.yml up -d
   ```

## Renew TLS Certificate
Certbot handles automatic renewals. To force a renewal or verify:
```bash
sudo certbot renew --dry-run
# To actually renew:
sudo certbot renew
```

## View Logs
To view logs of the backend service:
```bash
cd /opt/piyasapilot
docker compose -f docker/docker-compose.prod.yml logs -f backend
```
For other services, replace `backend` with `frontend` or `nginx-proxy`.

## CloudWatch Alarms
- **CPU > 80%**: Investigate background tasks or high traffic. Consider vertically scaling the EC2 instance or optimizing queries.
- **Disk > 80%**: Run cleanup on old logs or docker images (`docker system prune`). Expand EBS volume if needed.
