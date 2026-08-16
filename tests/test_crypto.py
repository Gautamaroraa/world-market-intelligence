import unittest

from pipelines.run_research import update_crypto_dashboard


class CryptoPipelineTests(unittest.TestCase):
    def test_live_snapshot_updates_without_crossing_risk_boundaries(self):
        dashboard = {"crypto": {"updatedAt": "2026-01-01T00:00:00+00:00", "score": 50, "dataMode": "DEMO", "assets": [{"symbol": "BTC", "score": 70, "signal": "HOLD"}]}}
        update_crypto_dashboard(dashboard, [{"symbol": "BTC", "price": 100000, "change24h": 2, "volume24h": 1234, "intradayRange": 4, "observedAt": "2026-08-16T10:00:00+00:00", "source": "Coinbase", "sourceUrl": "https://example.com"}])
        asset = dashboard["crypto"]["assets"][0]
        self.assertEqual(asset["price"], 100000)
        self.assertGreaterEqual(asset["score"], 0)
        self.assertLessEqual(asset["score"], 100)
        self.assertIn(asset["signal"], {"ACCUMULATE", "HOLD", "WATCH", "AVOID"})
        self.assertIn("LIVE COINBASE", dashboard["crypto"]["dataMode"])


if __name__ == "__main__":
    unittest.main()
