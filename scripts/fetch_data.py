"""CLI placeholder for data fetch jobs."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=False)
    parser.add_argument("--timeframe", default="1d")
    args = parser.parse_args()
    print(json.dumps({"symbol": args.symbol, "timeframe": args.timeframe, "status": "ready"}))


if __name__ == "__main__":
    main()
