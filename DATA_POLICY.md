# Evidence and data policy

The system stores three distinct times whenever a source exposes them:

1. the event occurrence time;
2. the publication or filing time;
3. the time the research pipeline first observed the record.

Only information available at or before a simulated decision timestamp may be
used in backtests. The dashboard must never silently rewrite historical source
times. Corrections are appended as new evidence records.

## Evidence states

- `CONFIRMED`: supported by an official primary source or corroborated by
  independent sources.
- `DEVELOPING`: reported but not yet sufficiently corroborated.
- `DISPUTED`: material sources conflict or a prior claim has been challenged.

GDELT is an event-discovery layer, not proof by itself. Every actionable thesis
must retain the original source URL and corroboration record.

## Decision boundary

Language models may classify, summarise and map evidence. Deterministic code
owns scoring thresholds, risk caps and portfolio allocation. The public
dashboard generates planning levels only and never places an order.

## Trading and derivatives boundary

- Spot quotes and futures telemetry are separate records; mark price must never
  be presented as the spot price.
- Crypto spot trade and futures mark-price WebSockets are rendered once per
  second. This is a display cadence, not a guarantee of tick completeness or an
  executable price.
- Crypto multi-timeframe structure uses 1m, 5m, 15m, 1h, 4h and 1d public
  candles and refreshes once per minute. A directional confirmation requires at
  least four aligned horizons and no opposing 1h, 4h or 1d structure.
- The dashboard must show `FEED REQUIRED` rather than infer NSE live prices or
  candles from stale snapshots when no licensed NSE/broker stream is present.
- Funding, open interest, index price and mark price may inform a model but do
  not prove future direction.
- Liquidation values shown in the browser are estimates. The connected venue's
  maintenance margin, fees, contract size and margin engine are authoritative.
- NSE lot sizes, eligible underlyings, expiries and margins must be read from an
  official exchange or authorised-broker feed at execution time.
- API keys, access tokens and account identifiers are prohibited in browser
  storage and the public repository.
- Live order submission remains disabled until a private execution service adds
  authentication, idempotency, audit logging, rate limits and explicit approval.
