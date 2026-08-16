import unittest

from pipelines.collectors.crypto import merge_quotes
from pipelines.run_research import update_crypto_dashboard


class CryptoPipelineTests(unittest.TestCase):
    def test_live_snapshot_updates_without_crossing_risk_boundaries(self):
        dashboard = {"crypto": {"updatedAt": "2026-01-01T00:00:00+00:00", "score": 50, "dataMode": "DEMO", "portfolioValue": 10000, "history": [10000], "assets": [{"symbol": "BTC", "price": 99000, "score": 70, "signal": "HOLD", "allocationCycle": 25}]}}
        update_crypto_dashboard(dashboard, [{"symbol": "BTC", "price": 100000, "change24h": 2, "volume24h": 1234, "intradayRange": 4, "observedAt": "2026-08-16T10:00:00+00:00", "source": "Coinbase + Kraken", "sourceUrl": "https://example.com", "feedQuality": "VERIFIED", "spreadBps": 2, "exchangePrices": {"Coinbase": 100010, "Kraken": 99990}, "futures": {"contract": "BTCUSDT", "markPrice": 100020, "indexPrice": 100000, "fundingRate": 0.01, "nextFundingTime": 1786900000000, "openInterest": 80000, "observedAt": "2026-08-16T10:00:00+00:00", "source": "Binance USD-M public market data"}}])
        asset = dashboard["crypto"]["assets"][0]
        self.assertEqual(asset["price"], 100000)
        self.assertGreaterEqual(asset["score"], 0)
        self.assertLessEqual(asset["score"], 100)
        self.assertIn(asset["signal"], {"ACCUMULATE", "HOLD", "WATCH", "AVOID"})
        self.assertIn("LIVE COINBASE", dashboard["crypto"]["dataMode"])
        self.assertEqual(asset["futures"]["contract"], "BTCUSDT")
        self.assertEqual(asset["futures"]["markPrice"], 100020)

    def test_cross_exchange_price_uses_median_and_marks_verified(self):
        quote = merge_quotes("BTC", [{"exchange":"Coinbase","price":100010,"open":99000,"high":101000,"low":98000,"volume":1000},{"exchange":"Kraken","price":99990,"open":99020,"high":100900,"low":98100,"volume":1100}], "2026-08-16T10:00:00+00:00")
        self.assertEqual(quote["price"], 100000)
        self.assertEqual(quote["feedQuality"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
