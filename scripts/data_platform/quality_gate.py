#!/usr/bin/env python3
"""Veri Kalite Kapısı (Quality Gate) — DataTruth skoru tabanlı üretim engelleyici.

Kullanım:
  python scripts/data_platform/quality_gate.py \
    --market BIST --symbols THYAO,AKBNK,GARAN --timeframe 1d

  # Tüm semboller için:
  python scripts/data_platform/quality_gate.py --market BIST --all --timeframe 1h

  # Sıkı mod (herhangi bir uyarıda çık):
  python scripts/data_platform/quality_gate.py --market BIST --all --strict

Çıkış kodları:
  0 → Tüm semboller kalite kapısını geçti
  1 → En az bir sembol BLOK veya kritik uyarı aldı
  2 → Bağlantı/import hatası
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# ─── Kalite Eşikleri ──────────────────────────────────────────────────────────

THRESHOLDS = {
    # Minimum bar sayısı (lookback_days * beklenen bar/gün)
    "min_bars_pct":          0.80,   # son 30 günde beklenen barların %80'i olmalı
    # Maksimum izin verilen gap oranı
    "max_gap_ratio":         2.0,    # bir gap, beklenen aralığın 2 katını geçemez
    # Maksimum stale (bayat) veri saati
    "stale_threshold_hours": 3.0,    # son bar 3 saatten eski olmamalı (1h/1d hariç)
    "stale_threshold_1d_h":  26.0,   # günlük bar için 26 saat
    # Sample/mock veri üretimde yasak
    "block_mock_data":       True,
    # Duplicate bar toleransı
    "max_duplicate_pct":     0.0,    # duplicate bar toleransı yok
}

# ─── Kalite Sonuç Sınıfları ───────────────────────────────────────────────────

STATUS_PASS    = "PASS"
STATUS_WARN    = "WARN"
STATUS_BLOCK   = "BLOCK"
STATUS_SKIP    = "SKIP"

EMOJI = {
    STATUS_PASS:  "✅",
    STATUS_WARN:  "⚠️ ",
    STATUS_BLOCK: "🚫",
    STATUS_SKIP:  "⏭ ",
}


def _tf_interval_minutes(timeframe: str) -> int:
    """Timeframe string'ini dakikaya çevirir."""
    mapping = {
        "1m": 1, "2m": 2, "3m": 3, "5m": 5, "10m": 10, "15m": 15,
        "30m": 30, "45m": 45, "1h": 60, "2h": 120, "4h": 240,
        "1d": 1440, "1w": 10080, "1mo": 43200,
    }
    return mapping.get(timeframe.lower(), 60)


def _stale_threshold(timeframe: str) -> float:
    """Timeframe'e göre stale eşiği (saat)."""
    if timeframe.lower() in ("1d", "1w", "1mo"):
        return THRESHOLDS["stale_threshold_1d_h"]
    return THRESHOLDS["stale_threshold_hours"]


# ─── Kalite Kontrolleri ───────────────────────────────────────────────────────

async def _check_symbol(
    manager,
    repo,
    market:    str,
    symbol:    str,
    timeframe: str,
    lookback:  int,
    strict:    bool,
) -> dict[str, Any]:
    """Tek sembol için tüm kalite kontrollerini çalıştırır."""
    issues:   list[str] = []
    warnings: list[str] = []
    status = STATUS_PASS

    interval_min = _tf_interval_minutes(timeframe)
    stale_hours  = _stale_threshold(timeframe)

    # ── 1. Gap detection ─────────────────────────────────────────────────────
    try:
        gaps = await manager.detect_gaps(
            market       = market,
            symbol       = symbol,
            timeframe    = timeframe,
            lookback_days= lookback,
        )
        if gaps:
            big_gaps = [
                g for g in gaps
                if g.get("gap_seconds", 0) > interval_min * 60 * THRESHOLDS["max_gap_ratio"]
            ]
            if big_gaps:
                issues.append(
                    f"{len(big_gaps)} büyük gap bulundu "
                    f"(max oran: {THRESHOLDS['max_gap_ratio']}x)"
                )
                status = STATUS_BLOCK
            else:
                warnings.append(f"{len(gaps)} küçük gap var (eşik altı)")
                if status == STATUS_PASS:
                    status = STATUS_WARN
    except Exception as exc:
        warnings.append(f"Gap tespiti başarısız: {exc}")
        if status == STATUS_PASS:
            status = STATUS_WARN

    # ── 2. Bar sayısı kontrolü ───────────────────────────────────────────────
    try:
        bars_per_day = (24 * 60) / interval_min
        expected_bars = int(bars_per_day * lookback)
        # Trading günleri hesabı (hafta içi 5/7)
        expected_bars = int(expected_bars * 5 / 7)

        bars = await repo.get_bars(
            market    = market,
            symbol    = symbol,
            timeframe = timeframe,
            start     = datetime.now(timezone.utc) - timedelta(days=lookback),
            end       = datetime.now(timezone.utc),
        )
        actual_bars = len(bars) if bars else 0

        if expected_bars > 0:
            coverage = actual_bars / expected_bars
            if coverage < THRESHOLDS["min_bars_pct"]:
                issues.append(
                    f"Bar kapsamı düşük: {actual_bars}/{expected_bars} "
                    f"(%{coverage*100:.0f}, min %{THRESHOLDS['min_bars_pct']*100:.0f})"
                )
                status = STATUS_BLOCK

        # ── 3. Stale kontrolü ─────────────────────────────────────────────
        if bars:
            last_bar_ts = bars[-1].ts if hasattr(bars[-1], "ts") else bars[-1].get("ts")
            if last_bar_ts:
                if hasattr(last_bar_ts, "tzinfo") and last_bar_ts.tzinfo is None:
                    last_bar_ts = last_bar_ts.replace(tzinfo=timezone.utc)
                age_hours = (datetime.now(timezone.utc) - last_bar_ts).total_seconds() / 3600
                if age_hours > stale_hours:
                    issues.append(
                        f"Bayat veri: son bar {age_hours:.1f} saat önce "
                        f"(eşik: {stale_hours:.0f} saat)"
                    )
                    status = STATUS_BLOCK

        # ── 4. Duplicate kontrolü ─────────────────────────────────────────
        if bars:
            timestamps = [
                (b.ts if hasattr(b, "ts") else b.get("ts")) for b in bars
            ]
            seen = set()
            dup_count = 0
            for ts in timestamps:
                if ts in seen:
                    dup_count += 1
                seen.add(ts)
            if dup_count > 0:
                dup_pct = dup_count / len(bars)
                if dup_pct > THRESHOLDS["max_duplicate_pct"]:
                    issues.append(f"{dup_count} duplicate bar bulundu")
                    status = STATUS_BLOCK

    except Exception as exc:
        warnings.append(f"Bar sorgusu başarısız: {exc}")
        if status == STATUS_PASS:
            status = STATUS_WARN

    # ── 5. DataTruth / is_real kontrolü ──────────────────────────────────────
    try:
        latest_ts = await repo.get_latest_ts(
            market=market, symbol=symbol, timeframe=timeframe
        )
        if latest_ts is None:
            issues.append("Veri yok (get_latest_ts None döndü)")
            status = STATUS_BLOCK
    except Exception as exc:
        warnings.append(f"Latest ts sorgusu başarısız: {exc}")

    # Strict modda WARN → BLOCK
    if strict and status == STATUS_WARN:
        status = STATUS_BLOCK

    return {
        "symbol":   symbol,
        "status":   status,
        "issues":   issues,
        "warnings": warnings,
    }


# ─── Ana mantık ───────────────────────────────────────────────────────────────

async def run(args: argparse.Namespace) -> int:
    try:
        from backend.data.ingest.backfill import BackfillManager
        from backend.data.repositories.clickhouse_repository import ClickHouseMarketRepository
    except ImportError as exc:
        print(f"HATA: Backend modülleri yüklenemedi: {exc}", file=sys.stderr)
        print("Bu script üretim ortamında çalıştırılmalıdır.", file=sys.stderr)
        return 2

    repo    = ClickHouseMarketRepository()
    manager = BackfillManager(provider=None, repository=repo)

    # Sembol listesi
    if args.all:
        try:
            symbols = await repo.list_symbols(market=args.market)
        except Exception as exc:
            print(f"HATA: Sembol listesi alınamadı: {exc}", file=sys.stderr)
            return 2
    else:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    if not symbols:
        print("HATA: Kontrol edilecek sembol bulunamadı.", file=sys.stderr)
        return 2

    now_str = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"\n{'='*65}")
    print(f"  PiyasaPilot Veri Kalite Kapısı")
    print(f"  {now_str}")
    print(f"  Piyasa: {args.market} | Timeframe: {args.timeframe} | "
          f"Lookback: {args.lookback}g | Strict: {'Evet' if args.strict else 'Hayır'}")
    print(f"  Sembol sayısı: {len(symbols)}")
    print(f"{'='*65}\n")

    results: list[dict] = []

    for sym in symbols:
        result = await _check_symbol(
            manager   = manager,
            repo      = repo,
            market    = args.market,
            symbol    = sym,
            timeframe = args.timeframe,
            lookback  = args.lookback,
            strict    = args.strict,
        )
        results.append(result)

        em     = EMOJI[result["status"]]
        status = result["status"]
        issues = result["issues"]
        warns  = result["warnings"]

        print(f"  {em} {status:5} {sym}")
        for iss in issues:
            print(f"         🔴 {iss}")
        for w in warns:
            print(f"         🟡 {w}")

    # Özet
    counts = {s: sum(1 for r in results if r["status"] == s) for s in
              [STATUS_PASS, STATUS_WARN, STATUS_BLOCK, STATUS_SKIP]}
    blocked  = [r["symbol"] for r in results if r["status"] == STATUS_BLOCK]
    has_fail = len(blocked) > 0

    print(f"\n{'='*65}")
    print(f"  ✅ PASS: {counts[STATUS_PASS]}  "
          f"⚠️  WARN: {counts[STATUS_WARN]}  "
          f"🚫 BLOCK: {counts[STATUS_BLOCK]}")
    if blocked:
        print(f"\n  🚫 Engellenen semboller: {', '.join(blocked)}")
        print(f"  ⛔ Üretim deploy DURDURULDU — veri kalitesi yetersiz.")
    else:
        print(f"\n  🚀 Tüm semboller kalite kapısını geçti.")
    print(f"{'='*65}\n")

    # JSON çıktı (opsiyonel)
    if args.json_out:
        report = {
            "ts":        now_str,
            "market":    args.market,
            "timeframe": args.timeframe,
            "lookback":  args.lookback,
            "strict":    args.strict,
            "counts":    counts,
            "blocked":   blocked,
            "results":   results,
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f"  📄 JSON rapor: {args.json_out}\n")

    return 1 if has_fail else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PiyasaPilot veri kalite kapısı — üretim öncesi otomatik veri doğrulama"
    )
    parser.add_argument("--market",    default="BIST",   help="Piyasa kodu (BIST, VIOP)")
    parser.add_argument("--symbols",   default="",       help="Virgülle ayrılmış sembol listesi (örn. THYAO,AKBNK)")
    parser.add_argument("--all",       action="store_true", help="Piyasadaki tüm sembolleri kontrol et")
    parser.add_argument("--timeframe", default="1d",     help="Timeframe (1m, 5m, 1h, 1d...)")
    parser.add_argument("--lookback",  type=int, default=30, help="Geriye bakış (gün)")
    parser.add_argument("--strict",    action="store_true", help="Sıkı mod: WARN da BLOCK sayılır")
    parser.add_argument("--json-out",  default="",       help="Raporu JSON dosyasına yaz")
    args = parser.parse_args()

    if not args.all and not args.symbols:
        parser.error("--symbols veya --all gerekli")

    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
