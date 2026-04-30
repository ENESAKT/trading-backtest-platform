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
    from quant_engine.research.lightgbm_model import readiness_from_bars

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/cache/ohlcv.sqlite3")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--min-rows", type=int, default=5_000)
    args = parser.parse_args()

    cache = OHLCVCache(db_path=args.db)
    bars = cache.get_window(args.symbol, args.interval, limit=max(args.min_rows + 30, 100))
    report = readiness_from_bars(bars, min_rows=args.min_rows).to_dict()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"ready", "insufficient_data", "dependency_missing"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
