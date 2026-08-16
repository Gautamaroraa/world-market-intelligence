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
    if "crypto" in payload:
        crypto = payload["crypto"]
        datetime.fromisoformat(crypto["updatedAt"])
        if not 0 <= crypto["score"] <= 100 or not 0 <= crypto["stableReserve"] <= 100:
            raise ValueError("Invalid crypto risk controls")
        if not crypto.get("history") or crypto.get("portfolioValue", 0) <= 0:
            raise ValueError("Crypto portfolio history is missing")
        symbols: set[str] = set()
        for asset in crypto["assets"]:
            if asset["symbol"] in symbols or not 0 <= asset["score"] <= 100:
                raise ValueError(f"Invalid crypto asset: {asset['symbol']}")
            if not 0 <= asset["allocationTactical"] <= 100 or not 0 <= asset["allocationCycle"] <= 100:
                raise ValueError(f"Invalid crypto allocation: {asset['symbol']}")
            futures = asset.get("futures")
            if futures and (futures.get("markPrice", 0) <= 0 or futures.get("indexPrice", 0) <= 0 or futures.get("openInterest", 0) < 0):
                raise ValueError(f"Invalid futures telemetry: {asset['symbol']}")
            symbols.add(asset["symbol"])
    print("Dashboard data validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
