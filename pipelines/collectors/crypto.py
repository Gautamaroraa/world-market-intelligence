from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PRODUCTS = {
    "BTC": {"coinbase": "BTC-USD", "kraken": "XBTUSD"},
    "ETH": {"coinbase": "ETH-USD", "kraken": "ETHUSD"},
    "SOL": {"coinbase": "SOL-USD", "kraken": "SOLUSD"},
    "LINK": {"coinbase": "LINK-USD", "kraken": "LINKUSD"},
    "AVAX": {"coinbase": "AVAX-USD", "kraken": "AVAXUSD"},
}


def _read_json(url: str, timeout: int) -> dict:
    request = Request(url, headers={"User-Agent": "world-market-intelligence/1.1"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _coinbase_quote(product: str, timeout: int) -> dict:
    row = _read_json(f"https://api.exchange.coinbase.com/products/{product}/stats", timeout)
    return {"exchange": "Coinbase", "price": float(row["last"]), "open": float(row["open"]), "high": float(row["high"]), "low": float(row["low"]), "volume": float(row["volume"])}


def _kraken_quote(pair: str, timeout: int) -> dict:
    payload = _read_json(f"https://api.kraken.com/0/public/Ticker?{urlencode({'pair': pair})}", timeout)
    if payload.get("error"):
        raise ValueError(", ".join(payload["error"]))
    row = next(iter(payload["result"].values()))
    return {"exchange": "Kraken", "price": float(row["c"][0]), "open": float(row["o"]), "high": float(row["h"][1]), "low": float(row["l"][1]), "volume": float(row["v"][1])}


def merge_quotes(symbol: str, quotes: list[dict], observed_at: str) -> dict | None:
    if not quotes:
        return None
    prices = [quote["price"] for quote in quotes]
    price = statistics.median(prices)
    spread_bps = round((max(prices) - min(prices)) / price * 10_000, 1) if len(prices) > 1 and price else 0
    quality = "VERIFIED" if len(prices) > 1 and spread_bps <= 100 else "ANOMALY" if len(prices) > 1 else "SINGLE SOURCE"
    opens = [quote["open"] for quote in quotes if quote["open"]]
    change = (price / statistics.median(opens) - 1) * 100 if opens else 0
    return {
        "symbol": symbol,
        "price": round(price, 8),
        "change24h": round(change, 2),
        "volume24h": round(statistics.median([quote["volume"] for quote in quotes]), 2),
        "intradayRange": round((max(quote["high"] for quote in quotes) - min(quote["low"] for quote in quotes)) / price * 100, 2) if price else 0,
        "observedAt": observed_at,
        "source": " + ".join(quote["exchange"] for quote in quotes),
        "sourceUrl": f"https://www.coinbase.com/price/{symbol.lower()}",
        "exchangePrices": {quote["exchange"]: quote["price"] for quote in quotes},
        "spreadBps": spread_bps,
        "feedQuality": quality,
    }


def collect_crypto_snapshot(timeout: int = 15) -> list[dict]:
    """Cross-check continuous USD spot prices from Coinbase and Kraken."""
    observed_at = datetime.now(timezone.utc).isoformat()
    snapshots: list[dict] = []
    for symbol, pairs in PRODUCTS.items():
        quotes: list[dict] = []
        for exchange, collector in (("Coinbase", lambda: _coinbase_quote(pairs["coinbase"], timeout)), ("Kraken", lambda: _kraken_quote(pairs["kraken"], timeout))):
            try:
                quotes.append(collector())
            except Exception as exc:
                print(f"{exchange} collection failed safely for {symbol}: {exc}")
        merged = merge_quotes(symbol, quotes, observed_at)
        if merged:
            snapshots.append(merged)
    return snapshots
