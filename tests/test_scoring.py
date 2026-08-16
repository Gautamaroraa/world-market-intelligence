import unittest

from pipelines.engine.scoring import decision_from_score, lexical_impact, score_security


class ScoringTests(unittest.TestCase):
    def test_impact_terms(self):
        self.assertGreater(lexical_impact("profit growth and expansion approval"), 0)
        self.assertLess(lexical_impact("loss decline after tariff disruption"), 0)

    def test_signal_boundaries(self):
        self.assertEqual(decision_from_score(84), "ACCUMULATE")
        self.assertEqual(decision_from_score(70), "HOLD")
        self.assertEqual(decision_from_score(42), "AVOID")

    def test_result_stays_bounded(self):
        result = score_security(99, 20, ["profit growth approval"] * 10, "short")
        self.assertLessEqual(result.score, 100)
        self.assertLessEqual(result.confidence, 92)


if __name__ == "__main__":
    unittest.main()
