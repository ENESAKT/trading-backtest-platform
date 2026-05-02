"""Import BIST30 daily history into the local Parquet store.

Usage:
    .venv/bin/python scripts/import_bist30_history.py --start 2015-01-01
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from pathlib import Path

from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.data.symbols import BIST_STOCKS  # noqa: E402
from quant_engine.data_pipeline.data_validator import DataValidator  # noqa: E402
from quant_engine.data_pipeline.fetcher import BISTFetcher  # noqa: E402
from quant_engine.data_pipeline.storage_manager import StorageManager  # noqa: E402


def _default_symbols() -> list[str]:
    stocks = [s.replace(".IS", "") for s in BIST_STOCKS]
    return sorted({*stocks, "XU030"})


def _parse_symbols(value: str | None) -> list[str]:
    if not value:
        return _default_symbols()
    return [
        item.strip().upper().replace(".IS", "")
        for item in value.split(",")
        if item.strip()
    ]


def import_symbols(
    symbols: Iterable[str],
    *,
    start: str,
    end: str | None,
    interval: str,
    mode: str,
) -> dict[str, int]:
    symbols = list(symbols)
    storage = StorageManager()
    fetcher = BISTFetcher(storage_manager=storage)
    validator = DataValidator(min_rows=50)
    results: dict[str, int] = {}

    try:
        for i, symbol in enumerate(symbols, 1):
            logger.info("[{}/{}] {} indiriliyor", i, len(symbols), symbol)
            df = fetcher.fetch_single(symbol, start=start, end=end, interval=interval)
            if df.empty:
                results[symbol] = 0
                continue

            validation = validator.validate(df, symbol)
            if not validation.is_valid:
                logger.warning(
                    "{} kalite kontrolünden geçemedi; otomatik düzeltme deneniyor.",
                    symbol,
                )
                df = DataValidator.auto_fix(df)

            rows = storage.write_symbol_data(df, symbol, mode=mode)
            results[symbol] = rows
    finally:
        storage.close()

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Import BIST30 daily history into data/bist.")
    parser.add_argument("--start", default="2015-01-01", help="YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="YYYY-MM-DD; omitted means today")
    parser.add_argument(
        "--interval",
        default="1d",
        choices=["1d"],
        help="Backtest history interval",
    )
    parser.add_argument("--mode", default="overwrite", choices=["overwrite", "append"])
    parser.add_argument(
        "--symbols",
        default=None,
        help="Comma separated symbols without .IS; omitted means BIST30 worker universe + XU030.",
    )
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    logger.info(
        "BIST tarihsel veri import başlıyor: {} sembol | {} -> {} | {}",
        len(symbols),
        args.start,
        args.end or "bugün",
        args.interval,
    )
    results = import_symbols(
        symbols,
        start=args.start,
        end=args.end,
        interval=args.interval,
        mode=args.mode,
    )
    ok = sum(1 for rows in results.values() if rows > 0)
    total = sum(results.values())
    logger.success("Import tamamlandı: {}/{} başarılı, {:,} satır", ok, len(results), total)
    for symbol, rows in sorted(results.items()):
        logger.info("{}: {:,} satır", symbol, rows)


if __name__ == "__main__":
    main()
