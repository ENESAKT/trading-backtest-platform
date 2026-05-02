# BACKFILL AND BACKUP RUNBOOK

## Veritabanı Yedekleme (Backup)

### ClickHouse
ClickHouse'daki `market_bars` tablosu devasa boyutlara ulaşabilir. 
Genelde ClickHouse'da veri *replicate* edilir ancak manuel yedek için disk snapshot'ı veya `clickhouse-backup` aracı kullanılabilir.
Daha küçük sistemlerde partition bazlı export:
`clickhouse-client --query="SELECT * FROM market_bars INTO OUTFILE 'backup_bars.parquet' FORMAT Parquet"`

### MySQL
MySQL metadata, envanter ve operasyonel işler için kullanılır, nispeten küçüktür.
Günlük mysqldump:
`mysqldump -u root -p piyasapilot > piyasapilot_meta_backup.sql`

### Redis
Redis cache amaçlıdır, kalıcı yedeğine gerek yoktur, istenirse AOF/RDB yedeklenebilir.

## Veri Kurtarma (Restore)

MySQL:
`mysql -u root -p piyasapilot < piyasapilot_meta_backup.sql`

ClickHouse Parquet Restore:
`clickhouse-client --query="INSERT INTO market_bars FORMAT Parquet" < backup_bars.parquet`

## Backfill Senaryoları

Eğer ClickHouse verisi tamamen uçar ve yedek yoksa;
1. Önce lokal yedek / duckDB (eğer varsa) içeri aktarılır.
2. `make backfill-bist100` çalıştırılır. (Geçmiş günlük ve üstü timeframeler için)
3. `make derive-timeframes` ile üst timeframeler üretilir.
4. Redis cache'leri otomatik temizlenecektir.
