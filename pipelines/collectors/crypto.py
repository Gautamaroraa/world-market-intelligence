from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen


PRODUCTS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "LINK": "LINK-USD",
    "AVAX": "AVAX-USD",
}


def collect_crypto_snapshot(timeout: int = 15) -> list[dict]:
    """Collect public Coinbase Exchange 24/7 spot statistics without credentials."""
    observed_at = datetime.now(timezone.utc).isoformat()
    snapshots: list[dict] = []
    for symbol, product in PRODUCTS.items():
        url = f"https://api.exchange.coinbase.com/products/{product}/stats"
        request = Request(url, headers={"User-Agent": "world-market-intelligence/1.0"})
        try:
            with urlopen(request, timeout=timeout) as response:
                row = json.load(response)
            price = float(row["last"])
            open_price = float(row["open"])
            high = float(row["high"])
            low = float(row["low"])
            snapshots.append({
                "symbol": symbol,
                "product": product,
                "price": price,
                "change24h": round((price / open_price - 1) * 100, 2) if open_price else 0,
                "volume24h": round(float(row["volume"]), 2),
                "intradayRange": round((high - low) / price * 100, 2) if price else 0,
                "observedAt": observed_at,
                "source": "Coinbase Exchange public market data",
                "sourceUrl": f"https://www.coinbase.com/price/{symbol.lower()}",
            })
        except Exception as exc:
            print(f"Crypto collection failed safely for {product}: {exc}")
    return snapshots
