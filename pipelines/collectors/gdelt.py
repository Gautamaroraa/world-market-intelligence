from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GDELT_DOC_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"


def _parse_seen_date(raw: str | None) -> str:
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    for pattern in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(raw, pattern).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()


def collect_articles(query: str, max_records: int = 75, timeout: int = 25) -> list[dict]:
    observed_at = datetime.now(timezone.utc).isoformat()
    params = urlencode({
        "query": query,
        "mode": "artlist",
        "maxrecords": max(1, min(max_records, 250)),
        "format": "json",
        "sort": "datedesc",
    })
    request = Request(
        f"{GDELT_DOC_ENDPOINT}?{params}",
        headers={"User-Agent": "WorldMarketIntelligence/0.1 (personal-research)"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)

    articles = []
    for item in payload.get("articles", []):
        url = item.get("url", "")
        title = (item.get("title") or "Untitled market event").strip()
        if not url:
            continue
        published_at = _parse_seen_date(item.get("seendate"))
        articles.append({
            "id": hashlib.sha256(url.encode("utf-8")).hexdigest()[:16],
            "timestamp": published_at,
            "publishedAt": published_at,
            "observedAt": observed_at,
            "eventAt": published_at,
            "title": title,
            "url": url,
            "source": item.get("domain") or "GDELT indexed source",
            "language": item.get("language") or "Unknown",
            "country": item.get("sourcecountry") or "GLOBAL",
            "tone": item.get("tone"),
        })
    return articles
