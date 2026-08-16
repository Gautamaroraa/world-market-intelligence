from __future__ import annotations

from dataclasses import dataclass


POSITIVE_TERMS = {"growth", "order", "profit", "upgrade", "investment", "expansion", "recovery", "approval"}
NEGATIVE_TERMS = {"decline", "loss", "downgrade", "investigation", "disruption", "inflation", "tariff", "default"}


@dataclass(frozen=True)
class ScoreResult:
    score: int
    confidence: int
    signal: str


def lexical_impact(text: str) -> int:
    words = {token.strip(".,:;!?()[]{}\"'").lower() for token in text.split()}
    return sum(term in words for term in POSITIVE_TERMS) - sum(term in words for term in NEGATIVE_TERMS)


def decision_from_score(score: int) -> str:
    if score >= 78:
        return "ACCUMULATE"
    if score >= 66:
        return "HOLD"
    if score >= 58:
        return "WATCH"
    if score >= 48:
        return "REDUCE"
    return "AVOID"


def score_security(base_score: int, price_change: float, related_headlines: list[str], horizon: str) -> ScoreResult:
    news_adjustment = max(-8, min(8, sum(lexical_impact(headline) for headline in related_headlines)))
    momentum_weight = 2.3 if horizon == "short" else 0.8
    momentum_adjustment = max(-8, min(8, round(price_change * momentum_weight)))
    score = max(0, min(100, round(base_score + news_adjustment + momentum_adjustment)))
    evidence_count = len(related_headlines)
    confidence = max(45, min(92, 58 + evidence_count * 3 + abs(news_adjustment)))
    return ScoreResult(score=score, confidence=confidence, signal=decision_from_score(score))
