"""Cache dolduğunda LightGBM modelini eğit.

Yetersiz veri veya eksik ``lightgbm`` paketi cron için kırıcı hata sayılmaz;
script JSON rapor üretir ve sahte model yazmaz.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from backend.data.cache import OHLCVCache
    from quant_engine.research.lightgbm_model import train_lightgbm_classifier

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/cache/ohlcv.sqlite3")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--min-rows", type=int, default=5_000)
    parser.add_argument("--output", default="models/lightgbm/BTCUSDT_15m.txt")
    parser.add_argument("--num-boost-round", type=int, default=60)
    args = parser.parse_args()

    cache = OHLCVCache(db_path=args.db)
    limit = max(args.min_rows + 60, 10_000)
    bars = cache.get_window(args.symbol, args.interval, limit=limit)
    result = train_lightgbm_classifier(
        bars,
        model_path=args.output,
        min_rows=args.min_rows,
        num_boost_round=args.num_boost_round,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status in {"trained", "insufficient_data", "dependency_missing"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
