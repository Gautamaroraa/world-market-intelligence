from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pipelines.collectors.gdelt import collect_articles
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


def update_dashboard(dashboard: dict, articles: list[dict]) -> dict:
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
    if not args.offline:
        try:
            articles = collect_articles(settings.gdelt_query, settings.gdelt_max_records, settings.request_timeout)
        except Exception as exc:
            print(f"GDELT collection failed safely: {exc}")
            return 0
    atomic_write(settings.output_path, update_dashboard(dashboard, articles))
    print(f"Research cycle complete: {len(articles)} articles, {settings.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
