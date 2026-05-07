"""CLI: python scripts/run_backtest.py --strategy <isim> --start 2024-01-01 --end 2024-12-31"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    args = parser.parse_args()
    print(json.dumps({"strategy": args.strategy, "start": args.start, "end": args.end, "status": "ready"}))


if __name__ == "__main__":
    main()
