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
owns scoring thresholds, risk caps and portfolio allocation. No signal may
place a live trade until it passes point-in-time backtesting and paper trading.
