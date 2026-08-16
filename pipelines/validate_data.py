from __future__ import annotations

import json
from datetime import datetime

from pipelines.config import settings


def main() -> int:
    payload = json.loads(settings.output_path.read_text(encoding="utf-8"))
    required = {"generatedAt", "market", "portfolio", "shortTerm", "longTerm", "events", "sectors"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"Dashboard data is missing keys: {sorted(missing)}")
    datetime.fromisoformat(payload["generatedAt"])
    for collection in (payload["shortTerm"], payload["longTerm"]):
        for stock in collection:
            if not 0 <= stock["score"] <= 100 or not 0 <= stock["confidence"] <= 100:
                raise ValueError(f"Invalid score for {stock['symbol']}")
    print("Dashboard data validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
