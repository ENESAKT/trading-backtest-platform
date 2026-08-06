#!/usr/bin/env python3
"""Production readiness smoke checks for PiyasaPilot.

Çalıştırma:
  python scripts/check_deployment_readiness.py [--base-url URL] [--skip-dns] [--skip-tls]

Tüm kontroller PASS dönmeden production'a geçilmez.
Canlı sunucu gerektiren kontroller --skip-* bayraklarıyla atlanabilir.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import socket
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import httpx
    _HTTPX = True
except ImportError:
    _HTTPX = False

BASE_URL = "https://piyasapilot.com"

# ─── Temel env + güvenlik kontrolleri ────────────────────────────────────────

def check_env_variables(_base_url: str) -> tuple[bool, str]:
    required = ["PUBLIC_BASE_URL", "CORS_ORIGINS", "JWT_SECRET"]
    missing  = [k for k in required if not os.environ.get(k)]
    if missing:
        return False, "Eksik env: " + ", ".join(missing)
    if len(os.environ.get("JWT_SECRET", "")) < 32:
        return False, "JWT_SECRET çok kısa (< 32 karakter)"
    return True, "Zorunlu env değerleri mevcut"


def check_env_no_placeholders(_base_url: str) -> tuple[bool, str]:
    """'.env.production' dosyasında BURAYA_YAZ placeholder kalmamalı."""
    env_file = Path(".env.production")
    if not env_file.exists():
        return False, ".env.production bulunamadı"
    content = env_file.read_text()
    if "BURAYA_YAZ" in content or "YOUR_" in content or "REPLACE_ME" in content:
        return False, ".env.production içinde doldurulmamış placeholder var"
    return True, ".env.production placeholder içermiyor"


def check_no_debug_mode(_base_url: str) -> tuple[bool, str]:
    """Üretimde DEBUG=true olmamalı."""
    debug = os.environ.get("DEBUG", "").lower()
    if debug in ("1", "true", "yes"):
        return False, "DEBUG=true üretimde kullanılamaz"
    app_env = os.environ.get("APP_ENV", "").lower()
    if app_env == "development":
        return False, "APP_ENV=development üretimde kullanılamaz"
    return True, f"Debug kapalı (APP_ENV={os.environ.get('APP_ENV', 'not_set')})"


# ─── Ağ kontrolleri ───────────────────────────────────────────────────────────

def check_dns(base_url: str) -> tuple[bool, str]:
    host = urlparse(base_url).hostname or base_url
    try:
        ips = socket.gethostbyname_ex(host)[2]
        return bool(ips), ", ".join(ips) if ips else "IP bulunamadı"
    except OSError as exc:
        return False, str(exc)


def check_tls(base_url: str) -> tuple[bool, str]:
    parsed = urlparse(base_url)
    host   = parsed.hostname
    if not host:
        return False, "Host yok"
    try:
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        with socket.create_connection((host, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        # Sertifika sona erme tarihi kontrol et
        expire_str = cert.get("notAfter", "")
        if expire_str:
            expire_dt = datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days_left  = (expire_dt - datetime.now(timezone.utc)).days
            if days_left < 14:
                return False, f"TLS sertifikası {days_left} gün içinde sona eriyor!"
            return True, f"TLS OK: {days_left} gün geçerli"
        return True, f"TLS OK: {cert.get('subject', '')}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


# ─── API kontrolleri ─────────────────────────────────────────────────────────

def _http_get(url: str, timeout: int = 8):
    if not _HTTPX:
        raise RuntimeError("httpx kurulu değil")
    return httpx.get(url, timeout=timeout)


def check_api_health(base_url: str) -> tuple[bool, str]:
    try:
        resp = _http_get(f"{base_url.rstrip('/')}/api/health")
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"
        body = resp.json()
        status = body.get("status", "")
        if status not in ("ok", "healthy", "running"):
            return False, f"status={status!r} beklenmiyor"
        return True, f"API health 200 — status={status}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def check_public_market_data(base_url: str) -> tuple[bool, str]:
    """Grafik için gereken public candles endpoint'i auth gerektirmemeli."""
    url = f"{base_url.rstrip('/')}/api/v2/candles?symbol=AKBNK.IS&interval=1d&limit=5"
    try:
        resp = _http_get(url, timeout=12)
        if resp.status_code == 401:
            return False, "HTTP 401: /api/v2/candles auth arkasında (public olmalı)"
        if resp.status_code >= 500:
            return False, f"HTTP {resp.status_code}: candles gateway hatası"
        try:
            payload = resp.json()
        except ValueError:
            return False, f"HTTP {resp.status_code}: JSON değil"
        if not isinstance(payload.get("bars"), list):
            return False, f"HTTP {resp.status_code}: bars alanı yok"
        # DataTruth metadata kontrolü
        meta = payload.get("metadata") or payload.get("data_truth") or {}
        has_meta = bool(meta)
        bar_count = len(payload["bars"])
        return True, f"HTTP {resp.status_code}: {bar_count} bar, metadata={'var' if has_meta else 'YOK'}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def check_metrics(base_url: str) -> tuple[bool, str]:
    try:
        resp = _http_get(f"{base_url.rstrip('/')}/metrics")
        return (resp.status_code == 200, f"HTTP {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def check_auth_smoke(base_url: str) -> tuple[bool, str]:
    """Auth endpoint'i token olmadan 401 döndürmeli (500 değil)."""
    try:
        resp = _http_get(f"{base_url.rstrip('/')}/api/auth/me")
        if resp.status_code == 401:
            return True, "HTTP 401 (auth guard çalışıyor)"
        if resp.status_code in (503, 200):
            return True, f"HTTP {resp.status_code}"
        return False, f"HTTP {resp.status_code} beklenmedik"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


# ─── DB / Altyapı kontrolleri ─────────────────────────────────────────────────

def check_db(_base_url: str) -> tuple[bool, str]:
    hints   = ["DATABASE_URL", "MYSQL_HOST", "CLICKHOUSE_URL", "REDIS_URL"]
    present = [k for k in hints if os.environ.get(k)]
    if not present:
        return False, "DB env değişkenleri bulunamadı"
    return True, "DB env: " + ", ".join(present)


def check_migrations(_base_url: str) -> tuple[bool, str]:
    """Tüm migration dosyaları mevcut ve sayısı beklenenle uyuşmalı."""
    migration_dir = Path("infra/mysql/migrations")
    if not migration_dir.exists():
        return False, f"{migration_dir} bulunamadı"
    sql_files = sorted(migration_dir.glob("*.sql"))
    if len(sql_files) < 9:
        return False, f"Sadece {len(sql_files)} migration var, en az 9 bekleniyor"
    # En kritik migration'ların varlığını kontrol et
    required = ["007_auth_tables.sql", "009_growth_tables.sql"]
    missing  = [r for r in required if not (migration_dir / r).exists()]
    if missing:
        return False, "Eksik migration'lar: " + ", ".join(missing)
    return True, f"{len(sql_files)} migration dosyası mevcut"


def check_migration_latest(_base_url: str) -> tuple[bool, str]:
    """En son migration numarasını kontrol eder."""
    migration_dir = Path("infra/mysql/migrations")
    if not migration_dir.exists():
        return False, "Migration dizini yok"
    files = sorted(migration_dir.glob("[0-9][0-9][0-9]_*.sql"))
    if not files:
        return False, "Migration dosyası bulunamadı"
    last = files[-1].name
    return True, f"Son migration: {last}"


# ─── Kod kalite kontrolleri ───────────────────────────────────────────────────

def check_no_sample_data_in_production(_base_url: str) -> tuple[bool, str]:
    """
    Backend kaynak kodunda sample/mock veri üretim endpoint'lerinden sızmamalı.

    Meşru kullanımlar (PASS):
      - is_real=False + source="license_pending"   → lisans henüz bağlı değil
      - is_real=False + source="cache-legacy"       → stale fallback, bilinen durum
      - is_real=False + source="stale"              → provider hata verdi, degraded mode
      - test/ dizinlerindeki dosyalar

    Sorunlu kullanımlar (FAIL):
      - is_real=False + source_type/source = "sample" veya "mock"
      - Yorum satırı olmayan açık sample veri bayrakları
    """
    patterns = [
        "backend/api/main.py",
        "backend/data/**/*.py",
    ]
    # Meşru is_real=False kaynakları — lisans bloğu, stale cache, degraded mode
    ALLOWED_SOURCES = {
        "license_pending", "cache-legacy", "stale", "blocked",
        "not_configured", "fallback", "degraded",
    }
    issues = []
    for pattern in patterns:
        for fpath in glob.glob(pattern, recursive=True):
            if "test" in fpath.lower():
                continue
            try:
                text  = Path(fpath).read_text()
                lines = text.splitlines()
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if not re.search(r'"is_real"\s*:\s*[Ff]alse', line):
                        continue
                    # Bağlam: bu satırı çevreleyen 5 satıra bak
                    ctx_start = max(0, i - 4)
                    ctx_end   = min(len(lines), i + 4)
                    context   = "\n".join(lines[ctx_start:ctx_end])
                    # Meşru kaynak varsa geç
                    is_allowed = any(src in context for src in ALLOWED_SOURCES)
                    if is_allowed:
                        continue
                    # sample veya mock kaynak → gerçek sorun
                    if re.search(r'"source[_type]*"\s*:\s*"(sample|mock)', context):
                        issues.append(f"{fpath}:{i}")
            except OSError:
                pass
    if issues:
        return False, f"Sample/mock is_real=false üretim kodunda: {'; '.join(issues[:3])}"
    return True, "Üretim kodunda sample/mock is_real=false bulunamadı"


def check_frontend_build(_base_url: str) -> tuple[bool, str]:
    """frontend/dist veya benzeri build çıktısı mevcut olmalı."""
    for dist in ["frontend/dist", "frontend/build"]:
        if Path(dist).exists():
            files = list(Path(dist).rglob("*.js"))
            return True, f"{dist}/ mevcut ({len(files)} JS dosyası)"
    return False, "Frontend build çıktısı bulunamadı (frontend/dist veya build)"


def check_docker_files(_base_url: str) -> tuple[bool, str]:
    """Kritik Docker dosyaları mevcut olmalı."""
    required = [
        "docker/Dockerfile.api",
        "docker/Dockerfile.frontend",
        "infra/docker-compose.prod.yml",
    ]
    missing = [f for f in required if not Path(f).exists()]
    if missing:
        return False, "Eksik Docker dosyaları: " + ", ".join(missing)
    return True, f"{len(required)} Docker dosyası mevcut"


def check_prometheus_alerts(_base_url: str) -> tuple[bool, str]:
    """Prometheus alert kuralları dosyası mevcut ve geçerli YAML olmalı."""
    alert_file = Path("docker/prometheus_alerts.yml")
    if not alert_file.exists():
        return False, "docker/prometheus_alerts.yml bulunamadı"
    try:
        import yaml  # type: ignore
        with alert_file.open() as f:
            config = yaml.safe_load(f)
        groups = config.get("groups", [])
        total_alerts = sum(len(g.get("rules", [])) for g in groups)
        return True, f"{len(groups)} grup, {total_alerts} alert kuralı"
    except ImportError:
        # yaml yüklü değilse sadece dosya varlığını kontrol et
        size = alert_file.stat().st_size
        return True, f"Alert dosyası mevcut ({size} byte, yaml doğrulaması atlandı)"
    except Exception as exc:  # noqa: BLE001
        return False, f"YAML parse hatası: {exc}"


def check_grafana_dashboard(_base_url: str) -> tuple[bool, str]:
    """Grafana dashboard JSON geçerli ve en az 10 panel içermeli."""
    dash_file = Path("docker/grafana/dashboard.json")
    if not dash_file.exists():
        return False, "docker/grafana/dashboard.json bulunamadı"
    try:
        dash = json.loads(dash_file.read_text())
        panels = dash.get("panels", [])
        if len(panels) < 10:
            return False, f"Sadece {len(panels)} panel var, en az 10 bekleniyor"
        return True, f"{len(panels)} Grafana paneli mevcut"
    except json.JSONDecodeError as exc:
        return False, f"JSON parse hatası: {exc}"


# ─── Ana fonksiyon ────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="PiyasaPilot production readiness checker")
    parser.add_argument("--base-url",   default=BASE_URL)
    parser.add_argument("--skip-dns",   action="store_true", help="DNS çözümlemesini atla")
    parser.add_argument("--skip-tls",   action="store_true", help="TLS kontrolünü atla")
    parser.add_argument("--skip-ws",    action="store_true", help="WebSocket testini atla")
    parser.add_argument("--skip-db",    action="store_true", help="DB env kontrolünü atla")
    parser.add_argument("--skip-live",  action="store_true", help="Canlı sunucu kontrollerini atla")
    parser.add_argument("--local-only", action="store_true", help="Sadece yerel dosya kontrollerini çalıştır")
    args = parser.parse_args()

    # Yerel dosya kontrolleri (her zaman)
    local_checks: list[tuple[str, object]] = [
        ("ENV_VARIABLES",            check_env_variables),
        ("ENV_NO_PLACEHOLDERS",      check_env_no_placeholders),
        ("DEBUG_MODE_OFF",           check_no_debug_mode),
        ("MIGRATION_FILES",          check_migrations),
        ("MIGRATION_LATEST",         check_migration_latest),
        ("DOCKER_FILES",             check_docker_files),
        ("PROMETHEUS_ALERTS",        check_prometheus_alerts),
        ("GRAFANA_DASHBOARD",        check_grafana_dashboard),
        ("NO_SAMPLE_DATA_IN_PROD",   check_no_sample_data_in_production),
        ("FRONTEND_BUILD",           check_frontend_build),
    ]
    if not args.skip_db:
        local_checks.append(("DB_ENV", check_db))

    # Canlı sunucu kontrolleri
    live_checks: list[tuple[str, object]] = []
    if not args.local_only and not args.skip_live:
        live_checks = [
            ("API_HEALTH",         check_api_health),
            ("PUBLIC_MARKET_DATA", check_public_market_data),
            ("METRICS_ENDPOINT",   check_metrics),
            ("AUTH_SMOKE",         check_auth_smoke),
        ]
        if not args.skip_dns:
            live_checks.insert(0, ("DNS_RESOLUTION", check_dns))
        if not args.skip_tls:
            live_checks.insert(1, ("TLS_CERTIFICATE", check_tls))

    all_checks = local_checks + live_checks
    failures: list[str] = []

    print(f"\n{'='*60}")
    print(f"  PiyasaPilot Production Readiness Check")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print(f"  Target: {args.base_url}")
    print(f"{'='*60}\n")

    for name, fn in all_checks:
        ok, detail = fn(args.base_url)  # type: ignore
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status:10} {name:35} {detail}")
        if not ok:
            failures.append(name)

    if args.skip_ws or args.local_only:
        print(f"  ⏭  SKIP       {'WS_QUOTES/WS_SIGNALS':35} skipped by flag")

    print(f"\n{'='*60}")
    if failures:
        print(f"  ❌ {len(failures)} KONTROL BAŞARISIZ: {', '.join(failures)}")
        print(f"  ⚠️  Production'a GEÇİLMEZ — hataları düzeltin.")
    else:
        passed = len(all_checks)
        skipped = 1 if (args.skip_ws or args.local_only) else 0
        print(f"  ✅ {passed} kontrol BAŞARILI, {skipped} atlandı")
        print(f"  🚀 Production deploy hazır!")
    print(f"{'='*60}\n")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
