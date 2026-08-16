from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pipelines.collectors.gdelt import collect_articles
from pipelines.collectors.crypto import collect_crypto_snapshot
from pipelines.config import settings
from pipelines.engine.scoring import lexical_impact, score_security


SYMBOL_TERMS = {
    "HDFCBANK": ("hdfc", "bank", "credit", "deposit"),
    "SBIN": ("sbi", "state bank", "bank", "credit"),
    "LT": ("larsen", "infrastructure", "construction", "capex", "order"),
    "SUNPHARMA": ("sun pharma", "pharma", "drug", "healthcare"),
    "RELIANCE": ("reliance", "refining", "telecom", "retail"),
    "TATASTEEL": ("tata steel", "steel", "metal", "iron ore"),
    "BHARTIARTL": ("bharti", "airtel", "telecom", "tariff"),
    "MARUTI": ("maruti", "automobile", "vehicle", "car sales"),
    "INFY": ("infosys", "technology", "software", "it spending"),
    "ONGC": ("ongc", "crude", "oil", "energy"),
    "BTC": ("bitcoin", "btc", "digital asset"),
    "ETH": ("ethereum", "ether", "eth"),
    "SOL": ("solana", "sol"),
    "LINK": ("chainlink", "link"),
    "AVAX": ("avalanche", "avax"),
    "XRP": ("xrp", "ripple"),
    "ADA": ("cardano", "ada"),
    "DOT": ("polkadot", "dot"),
    "LTC": ("litecoin", "ltc"),
    "UNI": ("uniswap", "uni", "decentralized exchange"),
    "ICICIBANK": ("icici", "bank", "credit", "deposit"),
    "TCS": ("tata consultancy", "tcs", "technology", "software"),
    "ITC": ("itc", "consumer", "cigarette", "fmcg"),
    "M&M": ("mahindra", "automobile", "tractor", "suv"),
    "NTPC": ("ntpc", "power", "electricity", "renewable"),
    "AXISBANK": ("axis bank", "bank", "credit", "deposit"),
    "TITAN": ("titan", "jewellery", "consumer", "watch"),
    "ADANIPORTS": ("adani ports", "port", "logistics", "cargo"),
    "POWERGRID": ("power grid", "transmission", "electricity"),
    "HINDUNILVR": ("hindustan unilever", "hul", "fmcg", "consumer"),
}

OFFICIAL_DOMAINS = ("rbi.org.in", "nseindia.com", "bseindia.com", "sebi.gov.in", "sec.gov", "gov.in")
STOPWORDS = {"after", "about", "with", "from", "that", "this", "into", "over", "amid", "market", "india", "indian"}


def load_dashboard(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def related_articles(symbol: str, articles: list[dict]) -> list[dict]:
    terms = SYMBOL_TERMS.get(symbol, (symbol.lower(),))
    return [article for article in articles if article.get("verificationStatus") == "CONFIRMED" and any(term in article["title"].lower() for term in terms)]


def corroboration_count(article: dict, articles: list[dict]) -> int:
    tokens = {word.strip(".,:;!?()[]{}\"'").lower() for word in article["title"].split()}
    tokens = {word for word in tokens if len(word) > 4 and word not in STOPWORDS}
    sources = {article["source"]}
    for candidate in articles:
        candidate_tokens = {word.strip(".,:;!?()[]{}\"'").lower() for word in candidate["title"].split()}
        if len(tokens & candidate_tokens) >= 3:
            sources.add(candidate["source"])
    return len(sources)


def event_from_article(article: dict, articles: list[dict]) -> dict:
    impact_score = lexical_impact(article["title"])
    impact = "POSITIVE" if impact_score > 0 else "NEGATIVE" if impact_score < 0 else "MIXED"
    companies = [symbol for symbol in SYMBOL_TERMS if any(term in article["title"].lower() for term in SYMBOL_TERMS[symbol])][:3]
    corroborated = corroboration_count(article, articles)
    official = any(domain in article["source"].lower() for domain in OFFICIAL_DOMAINS)
    status = "CONFIRMED" if official or corroborated >= 2 else "DEVELOPING"
    article["verificationStatus"] = status
    return {
        "id": f"gdelt-{article['id']}",
        "timestamp": article["timestamp"],
        "publishedAt": article.get("publishedAt", article["timestamp"]),
        "observedAt": article.get("observedAt", dashboard_timestamp()),
        "eventAt": article.get("eventAt", article["timestamp"]),
        "region": article["country"].upper(),
        "title": article["title"],
        "source": article["source"],
        "status": status,
        "impact": impact,
        "companies": companies or ["MARKET"],
        "summary": f"Indexed by GDELT with {corroborated} distinct source cluster(s). Market impact and company mappings are model inference.",
        "sourceUrl": article["url"],
        "sourceCount": corroborated,
        "confirmationBasis": "Official primary-source domain" if official else (f"Corroborated by {corroborated} distinct sources" if corroborated >= 2 else "Awaiting a second independent source"),
        "isInference": True,
    }


def dashboard_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def update_crypto_dashboard(dashboard: dict, snapshots: list[dict]) -> None:
    crypto = dashboard.get("crypto")
    if not crypto or not snapshots:
        return
    observed_at = max(item["observedAt"] for item in snapshots)
    by_symbol = {item["symbol"]: item for item in snapshots}
    scores: list[int] = []
    portfolio_step = 0.0
    portfolio_day = 0.0
    for asset in crypto.get("assets", []):
        snapshot = by_symbol.get(asset["symbol"])
        if not snapshot:
            continue
        momentum = max(-15, min(15, snapshot["change24h"] * 2.5))
        range_penalty = max(0, snapshot["intradayRange"] - 5) * 1.5
        previous_price = float(asset.get("price", snapshot["price"]))
        asset["price"] = snapshot["price"]
        asset["change24h"] = snapshot["change24h"]
        asset["volume24h"] = snapshot["volume24h"]
        asset["volatility"] = snapshot["intradayRange"]
        asset["observedAt"] = snapshot["observedAt"]
        asset["source"] = snapshot["source"]
        asset["sourceUrl"] = snapshot["sourceUrl"]
        asset["exchangePrices"] = snapshot.get("exchangePrices", {})
        asset["spreadBps"] = snapshot.get("spreadBps", 0)
        asset["feedQuality"] = snapshot.get("feedQuality", "SINGLE SOURCE")
        if snapshot.get("futures"):
            asset["futures"] = snapshot["futures"]
        asset["score"] = round(max(0, min(100, asset["score"] * 0.7 + 20 + momentum - range_penalty)))
        asset["signal"] = "ACCUMULATE" if asset["score"] >= 78 else "HOLD" if asset["score"] >= 62 else "WATCH" if asset["score"] >= 50 else "AVOID"
        scores.append(asset["score"])
        weight = float(asset.get("allocationCycle", 0)) / 100
        if previous_price:
            portfolio_step += weight * (snapshot["price"] / previous_price - 1)
        portfolio_day += weight * snapshot["change24h"]
    crypto["updatedAt"] = observed_at
    crypto["score"] = round(sum(scores) / len(scores)) if scores else crypto["score"]
    crypto["regime"] = "RISK-ON" if crypto["score"] >= 72 else "RISK-SELECTIVE" if crypto["score"] >= 55 else "RISK-OFF"
    crypto["portfolioValue"] = round(float(crypto.get("portfolioValue", 10_000)) * (1 + portfolio_step), 2)
    crypto["dayChange"] = round(portfolio_day, 2)
    history = list(crypto.get("history", []))
    history.append(crypto["portfolioValue"])
    crypto["history"] = history[-144:]
    if history:
        peak = history[0]
        drawdowns = []
        for value in history:
            peak = max(peak, value)
            drawdowns.append((value / peak - 1) * 100 if peak else 0)
        crypto["maxDrawdown"] = round(min(drawdowns), 2)
    qualities = [item.get("feedQuality") for item in snapshots]
    crypto["feedQuality"] = "VERIFIED" if qualities and all(item == "VERIFIED" for item in qualities) else "PARTIAL / CHECK REQUIRED"
    crypto["dataMode"] = "LIVE COINBASE + KRAKEN CROSS-CHECKED SPOT SNAPSHOT"


def update_dashboard(dashboard: dict, articles: list[dict], crypto_snapshots: list[dict] | None = None) -> dict:
    dashboard["generatedAt"] = datetime.now(timezone.utc).isoformat()
    if articles:
        verified_events = [event_from_article(article, articles) for article in articles]
        dashboard["events"] = verified_events[:8]
        dashboard["dataMode"] = "LIVE GDELT EVIDENCE · MARKET PRICES REMAIN SAMPLE"

    for key, horizon in (("shortTerm", "short"), ("longTerm", "long")):
        for stock in dashboard[key]:
            matches = related_articles(stock["symbol"], articles)
            result = score_security(stock["score"], stock["change"], [item["title"] for item in matches], horizon)
            stock["score"] = result.score
            stock["confidence"] = result.confidence
            stock["signal"] = result.signal
    update_crypto_dashboard(dashboard, crypto_snapshots or [])
    return dashboard


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix="dashboard-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        Path(temp_name).replace(path)
    finally:
        if Path(temp_name).exists():
            Path(temp_name).unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the dated market-research pipeline")
    parser.add_argument("--offline", action="store_true", help="Validate and rescore without network collection")
    args = parser.parse_args()
    dashboard = load_dashboard(settings.output_path)
    articles: list[dict] = []
    crypto_snapshots: list[dict] = []
    if not args.offline:
        try:
            articles = collect_articles(settings.gdelt_query, settings.gdelt_max_records, settings.request_timeout)
        except Exception as exc:
            print(f"GDELT collection failed safely: {exc}")
        crypto_snapshots = collect_crypto_snapshot(settings.request_timeout)
    atomic_write(settings.output_path, update_dashboard(dashboard, articles, crypto_snapshots))
    print(f"Research cycle complete: {len(articles)} articles, {len(crypto_snapshots)} crypto snapshots, {settings.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
