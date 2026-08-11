"""
High-Fidelity Real-Time Market Simulator.
Generates realistic live tick feeds, order book depth changes, volume bursts, and SMMA crossovers.
Used for testing, screen recording, and evaluation after market hours or without active API keys.
"""

import time
import math
import random
import threading
from datetime import datetime
from typing import List, Dict, Optional

from brokers.base_broker import BaseBroker
from core.data_models import TickData, MarketDepth, DepthLevel
import config


class LiveMarketSimulator(BaseBroker):
    def __init__(self, update_interval_sec: float = 0.5):
        super().__init__("Realistic Live NSE Feed Simulator")
        self.update_interval_sec = update_interval_sec
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None

        # Stock Initial Base Parameters
        self.stock_states: Dict[str, dict] = {}
        self._initialize_stock_states()

    def _initialize_stock_states(self):
        """Initialize initial price, trend, and depth profiles for NSE stocks."""
        profiles = [
            # Symbol, Base LTP, Trend, High Liquidity Flag (> 10 Lakhs)
            ("SUZLON", 42.50, 0.05, True),
            ("YESBANK", 34.20, -0.02, True),
            ("IRFC", 168.00, 0.12, True),
            ("NHPC", 94.50, 0.08, True),
            ("PNB", 112.40, -0.05, True),
            ("IDFCFIRSTB", 78.60, 0.03, True),
            ("SJVN", 125.10, 0.06, True),
            ("HUDCO", 285.30, 0.15, True),
            ("RENUKA", 44.80, -0.04, False),  # Liquidity < 10L (Filtered out)
            ("TRIDENT", 38.90, 0.01, False),   # Liquidity < 10L (Filtered out)
            ("SOUTHBANK", 28.50, 0.02, True),  # LTP < ₹30 (Price Filtered out)
            ("RELIANCE", 2950.0, 0.50, True),  # LTP > ₹500 (Price Filtered out)
            ("ZOMATO", 245.00, 0.20, True),
            ("TATASTEEL", 158.20, -0.10, True),
            ("NBCC", 118.50, 0.09, True),
        ]

        for symbol, base_ltp, trend, high_liq in profiles:
            self.stock_states[symbol] = {
                "ltp": base_ltp,
                "trend": trend,
                "high_liquidity": high_liq,
                "step": random.randint(0, 100),
                "cumulative_vol": random.randint(500_000, 2_000_000)
            }

    def fetch_historical_prices(self, symbol: str, interval: str = "1m", limit: int = 150) -> List[float]:
        """Generate realistic pre-seeded price history for initial SMMA 20/120 values."""
        state = self.stock_states.get(symbol, {"ltp": 100.0, "trend": 0.01})
        base = state["ltp"]
        trend = state["trend"]
        
        prices: List[float] = []
        curr = base - (limit * trend * 0.1)

        for i in range(limit):
            noise = random.gauss(0, 0.25)
            # Add sine wave pattern to create natural crossovers
            sine = math.sin(i / 15.0) * 0.8
            curr = max(5.0, curr + (trend * 0.05) + noise + sine)
            prices.append(round(curr, 2))

        return prices

    def connect(self) -> bool:
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._run_simulation_loop, daemon=True)
        self.worker_thread.start()
        print(f"[{self.name}] Live streaming simulation started.")
        return True

    def disconnect(self):
        self.is_running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
        print(f"[{self.name}] Simulation stopped.")

    def subscribe_symbols(self, symbols: List[str]):
        pass  # Simulator streams all configured stocks

    def _run_simulation_loop(self):
        """Continuous background tick loop."""
        while self.is_running:
            for symbol, st in self.stock_states.items():
                st["step"] += 1
                step = st["step"]

                # Price Walk Calculation
                change = random.gauss(0, 0.15) + (math.cos(step / 10.0) * 0.2)
                st["ltp"] = max(1.0, round(st["ltp"] + change, 2))
                
                tick_vol = random.randint(5_000, 45_000)
                st["cumulative_vol"] += tick_vol

                # Liquidity Generation (Bid & Ask Quantities)
                if st["high_liquidity"]:
                    # Fluctuate around 1,200,000 - 2,500,000 (Passes > 10 Lakhs filter)
                    bid_total = random.randint(1_050_000, 2_800_000)
                    ask_total = random.randint(1_020_000, 2_600_000)
                else:
                    # Low liquidity stock (Filtered out: Bid/Ask < 10 Lakhs)
                    bid_total = random.randint(200_000, 850_000)
                    ask_total = random.randint(150_000, 920_000)

                # Generate 5-level Market Depth
                bids = []
                ask_base = st["ltp"] + 0.05
                bid_base = st["ltp"] - 0.05

                for i in range(5):
                    bids.append(DepthLevel(
                        price=round(max(0.05, bid_base - (i * 0.05)), 2),
                        quantity=bid_total // 5 + random.randint(-10_000, 10_000),
                        orders=random.randint(12, 180)
                    ))

                asks = []
                for i in range(5):
                    asks.append(DepthLevel(
                        price=round(ask_base + (i * 0.05), 2),
                        quantity=ask_total // 5 + random.randint(-10_000, 10_000),
                        orders=random.randint(15, 210)
                    ))

                depth = MarketDepth(
                    bids=bids,
                    asks=asks,
                    total_bid_quantity=bid_total,
                    total_ask_quantity=ask_total
                )

                tick = TickData(
                    symbol=symbol,
                    ltp=st["ltp"],
                    volume=tick_vol,
                    timestamp=datetime.now(),
                    depth=depth
                )

                self._emit_tick(tick)

            time.sleep(self.update_interval_sec)
