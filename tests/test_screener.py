import unittest
from datetime import datetime
from core.data_models import TickData, MarketDepth, DepthLevel, CrossoverSignal, CrossoverType, SignalDecision
from core.screener import StockScreenerEngine
from ai.crossover_ml import SMMACrossoverMLEngine
import config


class TestStockScreener(unittest.TestCase):
    def setUp(self):
        self.screener = StockScreenerEngine()
        self.ai_engine = SMMACrossoverMLEngine()

    def test_ltp_and_liquidity_filters(self):
        # 1. Stock passing all filters (LTP ₹150, Bid/Ask 1.5M > 10L)
        tick_pass = TickData(
            symbol="GOOD_STOCK",
            ltp=150.0,
            volume=50000,
            timestamp=datetime.now(),
            depth=MarketDepth(
                total_bid_quantity=1_500_000,
                total_ask_quantity=1_200_000
            )
        )
        metrics_pass, _ = self.screener.process_tick(tick_pass)
        self.assertTrue(metrics_pass.passes_ltp_filter)
        self.assertTrue(metrics_pass.passes_liquidity_filter)
        self.assertTrue(metrics_pass.passes_all_filters)

        # 2. Stock failing LTP filter (LTP ₹25 < ₹30)
        tick_low_price = TickData(
            symbol="PENNY_STOCK",
            ltp=25.0,
            volume=10000,
            timestamp=datetime.now(),
            depth=MarketDepth(
                total_bid_quantity=2_000_000,
                total_ask_quantity=2_000_000
            )
        )
        metrics_low_p, _ = self.screener.process_tick(tick_low_price)
        self.assertFalse(metrics_low_p.passes_ltp_filter)
        self.assertFalse(metrics_low_p.passes_all_filters)

        # 3. Stock failing Liquidity filter (Bid Qty 500k < 10L)
        tick_low_liq = TickData(
            symbol="ILLIQUID_STOCK",
            ltp=100.0,
            volume=5000,
            timestamp=datetime.now(),
            depth=MarketDepth(
                total_bid_quantity=500_000,
                total_ask_quantity=1_500_000
            )
        )
        metrics_low_l, _ = self.screener.process_tick(tick_low_liq)
        self.assertFalse(metrics_low_l.passes_liquidity_filter)
        self.assertFalse(metrics_low_l.passes_all_filters)

    def test_ai_reasoning_evaluator(self):
        signal = CrossoverSignal(
            symbol="GOOD_STOCK",
            crossover_type=CrossoverType.BUY,
            smma_20=151.0,
            smma_120=148.0,
            ltp=152.0,
            timestamp=datetime.now()
        )
        
        # Test tick with strong bid wall and high volume
        tick = TickData(
            symbol="GOOD_STOCK",
            ltp=152.0,
            volume=100000,
            timestamp=datetime.now(),
            depth=MarketDepth(
                total_bid_quantity=2_500_000,
                total_ask_quantity=1_200_000
            )
        )
        metrics, _ = self.screener.process_tick(tick)

        prediction = self.ai_engine.evaluate_crossover(signal, metrics)
        self.assertIn(prediction.decision, [SignalDecision.ACCEPT, SignalDecision.AVOID])
        self.assertTrue(len(prediction.reasons) > 0)
        self.assertGreaterEqual(prediction.win_probability, 0.0)
        self.assertLessEqual(prediction.win_probability, 100.0)


if __name__ == "__main__":
    unittest.main()
