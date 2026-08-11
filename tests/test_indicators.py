import unittest
from datetime import datetime
from core.indicators import calculate_smma_series, SMMATracker
from core.data_models import CrossoverType


class TestSMMAIndicators(unittest.TestCase):
    def test_smma_calculation(self):
        prices = [float(i) for i in range(1, 30)]
        smma_20 = calculate_smma_series(prices, period=20)
        
        # SMMA at index 19 (first 20 elements) should equal SMA
        expected_sma_20 = sum(prices[:20]) / 20.0
        self.assertAlmostEqual(smma_20[19], expected_sma_20, places=4)

        # SMMA at index 20 should follow SMMA formula: (prev * 19 + price) / 20
        expected_smma_21 = (expected_sma_20 * 19 + prices[20]) / 20.0
        self.assertAlmostEqual(smma_20[20], expected_smma_21, places=4)

    def test_crossover_detection(self):
        tracker = SMMATracker("TEST_STOCK", fast_period=5, slow_period=10)
        
        # Seed 10 prices where fast < slow
        seed_prices = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
        tracker.seed_data(seed_prices)

        # Push prices up to trigger a Bullish Buy crossover (Fast SMMA crosses above Slow SMMA)
        signal = None
        for p in [15.0, 20.0, 25.0, 30.0]:
            fast, slow, sig = tracker.update(p, datetime.now())
            if sig:
                signal = sig

        self.assertIsNotNone(signal)
        self.assertEqual(signal.crossover_type, CrossoverType.BUY)


if __name__ == "__main__":
    unittest.main()
