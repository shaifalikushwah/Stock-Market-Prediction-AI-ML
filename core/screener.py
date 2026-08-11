from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import config
from core.data_models import TickData, StockMetrics, MarketDepth
from core.indicators import SMMATracker


class StockScreenerEngine:
    def __init__(self):
        # Symbol -> SMMATracker
        self.smma_trackers: Dict[str, SMMATracker] = {}
        # Symbol -> Deque of (timestamp, ltp, tick_volume)
        self.tick_buffers: Dict[str, deque] = {}
        # Symbol -> Latest StockMetrics
        self.latest_metrics: Dict[str, StockMetrics] = {}

    def register_symbol(self, symbol: str, initial_prices: Optional[List[float]] = None):
        """Register a symbol for screening and indicator tracking."""
        tracker = SMMATracker(symbol, config.SMMA_FAST_PERIOD, config.SMMA_SLOW_PERIOD)
        if initial_prices:
            tracker.seed_data(initial_prices)
        self.smma_trackers[symbol] = tracker
        self.tick_buffers[symbol] = deque()

    def process_tick(self, tick: TickData) -> Tuple[StockMetrics, Optional[object]]:
        """
        Process an incoming live market tick for a stock.
        Returns (StockMetrics, Optional[CrossoverSignal]).
        """
        symbol = tick.symbol
        if symbol not in self.smma_trackers:
            self.register_symbol(symbol)

        # 1. Update Tick History Buffer
        buffer = self.tick_buffers[symbol]
        buffer.append((tick.timestamp, tick.ltp, tick.volume))

        # Evict ticks older than 65 minutes to keep memory clean
        cutoff_65m = tick.timestamp - timedelta(minutes=65)
        while buffer and buffer[0][0] < cutoff_65m:
            buffer.popleft()

        # 2. Compute Rolling Metrics (Volume 5m/20m/60m & Avg LTP 20m/60m)
        vol_5m = 0
        vol_20m = 0
        vol_60m = 0
        
        sum_price_20m = 0.0
        count_20m = 0
        sum_price_60m = 0.0
        count_60m = 0

        t_5m = tick.timestamp - timedelta(minutes=5)
        t_20m = tick.timestamp - timedelta(minutes=20)
        t_60m = tick.timestamp - timedelta(minutes=60)

        for ts, price, vol in buffer:
            if ts >= t_60m:
                vol_60m += vol
                sum_price_60m += price
                count_60m += 1

            if ts >= t_20m:
                vol_20m += vol
                sum_price_20m += price
                count_20m += 1

            if ts >= t_5m:
                vol_5m += vol

        avg_20m = (sum_price_20m / count_20m) if count_20m > 0 else tick.ltp
        avg_60m = (sum_price_60m / count_60m) if count_60m > 0 else tick.ltp

        # 3. Calculate SMMA(20) & SMMA(120) and Crossover
        tracker = self.smma_trackers[symbol]
        smma_20, smma_120, signal = tracker.update(tick.ltp, tick.timestamp)

        # 4. Check Filtering Criteria
        passes_ltp = config.LTP_MIN <= tick.ltp <= config.LTP_MAX
        passes_liquidity = (
            tick.depth.total_bid_quantity >= config.LIQUIDITY_BID_MIN and
            tick.depth.total_ask_quantity >= config.LIQUIDITY_ASK_MIN
        )

        # 5. Construct StockMetrics object
        metrics = StockMetrics(
            symbol=symbol,
            ltp=tick.ltp,
            total_bid_qty=tick.depth.total_bid_quantity,
            total_ask_qty=tick.depth.total_ask_quantity,
            smma_20=smma_20,
            smma_120=smma_120,
            vol_5m=vol_5m,
            vol_20m=vol_20m,
            vol_60m=vol_60m,
            avg_price_20m=avg_20m,
            avg_price_60m=avg_60m,
            market_depth=tick.depth,
            passes_ltp_filter=passes_ltp,
            passes_liquidity_filter=passes_liquidity
        )

        self.latest_metrics[symbol] = metrics
        return metrics, signal

    def get_screened_stocks(self) -> List[StockMetrics]:
        """Return all stocks currently passing both LTP and Liquidity filters."""
        return [
            m for m in self.latest_metrics.values()
            if m.passes_all_filters
        ]
