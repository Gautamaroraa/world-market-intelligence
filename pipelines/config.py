from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_PATH = ROOT / "public" / "data" / "dashboard.json"


@dataclass(frozen=True)
class Settings:
    gdelt_query: str = os.getenv(
        "GDELT_QUERY",
        '((India OR "Indian economy" OR RBI OR NSE) '
        '(stocks OR earnings OR inflation OR rates OR oil OR policy OR exports)) '
        'OR ((Bitcoin OR Ethereum OR Solana OR crypto OR stablecoin) '
        '(regulation OR ETF OR exchange OR adoption OR security OR liquidation))',
    )
    gdelt_max_records: int = int(os.getenv("GDELT_MAX_RECORDS", "75"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "25"))
    minimum_source_count: int = int(os.getenv("MINIMUM_SOURCE_COUNT", "1"))
    output_path: Path = DASHBOARD_PATH


settings = Settings()
