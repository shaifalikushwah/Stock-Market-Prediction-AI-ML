"""
Abstract Base Class for Broker Connectors (Angel One, Fyers, and Live Simulator).
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional
from core.data_models import TickData


class BaseBroker(ABC):
    """
    Abstract interface for streaming live ticks and market depth.
    """
    def __init__(self, name: str):
        self.name = name
        self.tick_callbacks: List[Callable[[TickData], None]] = []

    def add_tick_callback(self, callback: Callable[[TickData], None]):
        """Register a callback function to handle incoming ticks."""
        self.tick_callbacks.append(callback)

    def _emit_tick(self, tick: TickData):
        """Internal helper to dispatch ticks to all registered callbacks."""
        for cb in self.tick_callbacks:
            try:
                cb(tick)
            except Exception as e:
                print(f"[{self.name}] Error in tick callback: {e}")

    @abstractmethod
    def connect(self) -> bool:
        """Connect to broker API / WebSocket stream."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from broker stream."""
        pass

    @abstractmethod
    def subscribe_symbols(self, symbols: List[str]):
        """Subscribe to live market feed for given symbols."""
        pass

    @abstractmethod
    def fetch_historical_prices(self, symbol: str, interval: str = "1m", limit: int = 150) -> List[float]:
        """Fetch historical price series to seed indicators."""
        pass
