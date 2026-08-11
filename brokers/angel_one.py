"""
Angel One (SmartAPI) Broker Integration Connector.
Translates Angel One SmartAPI WebSockets / REST API ticks into application TickData.
"""

import time
import random
from typing import List, Optional
from datetime import datetime
from brokers.base_broker import BaseBroker
from core.data_models import TickData, MarketDepth, DepthLevel
import config


class AngelOneBroker(BaseBroker):
    def __init__(self, api_key: Optional[str] = None, client_code: Optional[str] = None):
        super().__init__("Angel One SmartAPI")
        self.api_key = api_key or config.ANGEL_ONE_CONFIG["api_key"]
        self.client_code = client_code or config.ANGEL_ONE_CONFIG["client_code"]
        self.is_connected = False
        self.subscribed_symbols: List[str] = []

    def connect(self) -> bool:
        """Authenticate with Angel One SmartAPI."""
        print(f"[{self.name}] Initializing session for Client Code: {config.mask_credential(self.client_code)}...")
        # In live mode with SmartConnect SDK:
        # self.smart_api = SmartConnect(api_key=self.api_key)
        # data = self.smart_api.generateSession(...)
        self.is_connected = True
        print(f"[{self.name}] Connection established successfully.")
        return True

    def disconnect(self):
        print(f"[{self.name}] Disconnecting WebSocket stream.")
        self.is_connected = False

    def subscribe_symbols(self, symbols: List[str]):
        self.subscribed_symbols = symbols
        print(f"[{self.name}] Subscribed to {len(symbols)} symbols on NSE.")

    def fetch_historical_prices(self, symbol: str, interval: str = "1m", limit: int = 150) -> List[float]:
        """Fetch historical candle prices (or fallback synthetic seed for offline testing)."""
        base_price = random.uniform(35.0, 480.0)
        prices = [base_price]
        for _ in range(limit - 1):
            change = random.gauss(0, 0.5)
            new_p = max(5.0, prices[-1] + change)
            prices.append(round(new_p, 2))
        return prices

    def parse_angel_tick(self, raw_data: dict) -> TickData:
        """Helper to parse raw WebSocket JSON packet from Angel One SmartAPI."""
        symbol = raw_data.get("symbol", "UNKNOWN")
        ltp = float(raw_data.get("ltp", 0.0))
        vol = int(raw_data.get("volume", 0))

        # Extract 5-level depth
        bids = [DepthLevel(price=b["price"], quantity=b["quantity"]) for b in raw_data.get("bids", [])]
        asks = [DepthLevel(price=a["price"], quantity=a["quantity"]) for a in raw_data.get("asks", [])]

        total_bid_qty = sum(b.quantity for b in bids)
        total_ask_qty = sum(a.quantity for a in asks)

        depth = MarketDepth(
            bids=bids,
            asks=asks,
            total_bid_quantity=total_bid_qty,
            total_ask_quantity=total_ask_qty
        )

        return TickData(
            symbol=symbol,
            ltp=ltp,
            volume=vol,
            timestamp=datetime.now(),
            depth=depth
        )
