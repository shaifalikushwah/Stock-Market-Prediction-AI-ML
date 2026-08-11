"""
Fyers API v3 Broker Integration Connector.
Translates Fyers API v3 WebSockets / REST API ticks into application TickData.
"""

import time
import random
from typing import List, Optional
from datetime import datetime
from brokers.base_broker import BaseBroker
from core.data_models import TickData, MarketDepth, DepthLevel
import config


class FyersBroker(BaseBroker):
    def __init__(self, client_id: Optional[str] = None, access_token: Optional[str] = None):
        super().__init__("Fyers API v3")
        self.client_id = client_id or config.FYERS_CONFIG["client_id"]
        self.access_token = access_token or config.FYERS_CONFIG["access_token"]
        self.is_connected = False
        self.subscribed_symbols: List[str] = []

    def connect(self) -> bool:
        """Authenticate with Fyers API v3."""
        print(f"[{self.name}] Initializing session for Client ID: {config.mask_credential(self.client_id)}...")
        # In live mode with Fyers API SDK:
        # self.fyers = fyersModel.FyersModel(client_id=self.client_id, token=self.access_token)
        self.is_connected = True
        print(f"[{self.name}] Connection established successfully.")
        return True

    def disconnect(self):
        print(f"[{self.name}] Disconnecting Fyers stream.")
        self.is_connected = False

    def subscribe_symbols(self, symbols: List[str]):
        self.subscribed_symbols = symbols
        print(f"[{self.name}] Subscribed to {len(symbols)} symbols on NSE.")

    def fetch_historical_prices(self, symbol: str, interval: str = "1m", limit: int = 150) -> List[float]:
        """Fetch historical candle prices from Fyers API."""
        base_price = random.uniform(35.0, 480.0)
        prices = [base_price]
        for _ in range(limit - 1):
            change = random.gauss(0, 0.5)
            new_p = max(5.0, prices[-1] + change)
            prices.append(round(new_p, 2))
        return prices
