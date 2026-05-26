#!/usr/bin/env python3
"""Veri Gap Raporu — BackfillManager.detect_gaps çağırır.

Kullanım:
  python scripts/data_platform/gap_report.py \
    --market BIST --symbol THYAO --timeframe 1h --lookback 30

Çıktı: Her gap için start, end, gap_süresi ve beklenen süre yazdırır.
execute=True ile otomatik backfill başlatılabilir.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import os

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


async def run(args: argparse.Namespace) -> int:
    try:
        from backend.data.ingest.backfill import BackfillManager
        from backend.data.repositories.clickhouse_repository import ClickHouseMarketRepository
    except ImportError as exc:
        print(f"HATA: Backend modülleri yüklenemedi: {exc}", file=sys.stderr)
        print("Bu script üretim ortamında çalıştırılmalıdır.", file=sys.stderr)
        return 1

    repo    = ClickHouseMarketRepository()
    manager = BackfillManager(provider=None, repository=repo)

    print(f"\n📊 Gap Raporu: {args.market}/{args.symbol}/{args.timeframe} "
          f"(son {args.lookback} gün)\n")

    gaps = await manager.detect_gaps(
        market       = args.market,
        symbol       = args.symbol,
        timeframe    = args.timeframe,
        lookback_days= args.lookback,
    )

    if not gaps:
        print("✅ Gap bulunamadı — veri tam.")
        return 0

    print(f"⚠️  {len(gaps)} gap bulundu:\n")
    for i, g in enumerate(gaps, 1):
        start   = g["start"].isoformat() if hasattr(g["start"], "isoformat") else str(g["start"])
        end     = g["end"].isoformat()   if hasattr(g["end"], "isoformat")   else str(g["end"])
        gap_h   = g["gap_seconds"] / 3600
        exp_h   = g.get("expected_seconds", 0) / 3600
        print(f"  [{i:3}] {start} → {end}")
        print(f"         Süre: {gap_h:.1f}s (beklenen: {exp_h:.1f}s, oran: {gap_h/exp_h:.1f}x)\n")

    if args.fix:
        print("\n🔧 Backfill başlatılıyor...\n")
        from backend.data.ingest.backfill import BackfillManager as BM2

        # Gerçek provider gerekecek — buraya matriks/foreks provider'ı bağlanır
        print("❌ --fix: Gerçek provider henüz bağlı değil.")
        print("   backend/data/ingest/backfill.py içine provider bağlantısını ekleyin.")
        return 1

    print(f"\n💡 Gidermek için: --fix bayrağı ile tekrar çalıştırın.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="PiyasaPilot veri gap raporu")
    parser.add_argument("--market",    default="BIST",  help="Piyasa kodu (BIST, VIOP)")
    parser.add_argument("--symbol",    default="THYAO", help="Sembol")
    parser.add_argument("--timeframe", default="1h",    help="Timeframe (1m, 5m, 1h, 1d...)")
    parser.add_argument("--lookback",  type=int, default=30, help="Geriye bakış (gün)")
    parser.add_argument("--fix",       action="store_true",  help="Bulunan gapleri backfill et")
    args = parser.parse_args()

    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
