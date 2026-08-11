"""
Data models and dataclasses for Stock Market Screening and Analysis System.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional


class CrossoverType(Enum):
    NONE = "NONE"
    BUY = "BUY"    # SMMA(20) crosses above SMMA(120)
    SELL = "SELL"  # SMMA(20) crosses below SMMA(120)


class SignalDecision(Enum):
    ACCEPT = "ACCEPT"
    AVOID = "AVOID"


@dataclass
class DepthLevel:
    price: float
    quantity: int
    orders: int = 1


@dataclass
class MarketDepth:
    bids: List[DepthLevel] = field(default_factory=list)
    asks: List[DepthLevel] = field(default_factory=list)
    total_bid_quantity: int = 0
    total_ask_quantity: int = 0

    @property
    def top_bid_price(self) -> float:
        return self.bids[0].price if self.bids else 0.0

    @property
    def top_ask_price(self) -> float:
        return self.asks[0].price if self.asks else 0.0


@dataclass
class TickData:
    symbol: str
    ltp: float
    volume: int
    timestamp: datetime
    depth: MarketDepth


@dataclass
class StockMetrics:
    symbol: str
    ltp: float
    total_bid_qty: int
    total_ask_qty: int
    smma_20: float
    smma_120: float
    vol_5m: int
    vol_20m: int
    vol_60m: int
    avg_price_20m: float
    avg_price_60m: float
    market_depth: MarketDepth
    passes_ltp_filter: bool
    passes_liquidity_filter: bool

    @property
    def passes_all_filters(self) -> bool:
        return self.passes_ltp_filter and self.passes_liquidity_filter


@dataclass
class CrossoverSignal:
    symbol: str
    crossover_type: CrossoverType
    smma_20: float
    smma_120: float
    ltp: float
    timestamp: datetime


@dataclass
class AIPrediction:
    symbol: str
    crossover_type: CrossoverType
    decision: SignalDecision
    win_probability: float  # 0.0 to 100.0 %
    reasons: List[str]
    metrics_snapshot: Dict[str, float]
