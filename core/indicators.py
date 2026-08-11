from typing import List, Tuple, Optional
from core.data_models import CrossoverType, CrossoverSignal, datetime


def calculate_smma_series(prices: List[float], period: int) -> List[float]:
    """
    Calculates Smoothed Moving Average (SMMA) over a price series.
    SMMA_1 = SMA(prices[:period])
    SMMA_i = (SMMA_{i-1} * (period - 1) + Price_i) / period
    """
    if len(prices) < period:
        return [0.0] * len(prices)

    smma_values: List[float] = [0.0] * len(prices)
    
    # First value is standard SMA
    first_sma = sum(prices[:period]) / period
    smma_values[period - 1] = first_sma

    prev_smma = first_sma
    for i in range(period, len(prices)):
        curr_smma = (prev_smma * (period - 1) + prices[i]) / period
        smma_values[i] = curr_smma
        prev_smma = curr_smma

    return smma_values


class SMMATracker:
    """
    Maintains state for real-time incremental SMMA(20) and SMMA(120) calculation.
    """
    def __init__(self, symbol: str, fast_period: int = 20, slow_period: int = 120):
        self.symbol = symbol
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.prices: List[float] = []
        self.prev_fast_smma: float = 0.0
        self.prev_slow_smma: float = 0.0
        self.curr_fast_smma: float = 0.0
        self.curr_slow_smma: float = 0.0
        self.prev_crossover: CrossoverType = CrossoverType.NONE

    def seed_data(self, price_series: List[float]):
        """Seed tracker with historical price series (e.g. 1-minute closes)."""
        self.prices = list(price_series)
        n = len(self.prices)
        if n >= self.fast_period:
            # Calculate fast SMMA
            fast_val = sum(self.prices[:self.fast_period]) / self.fast_period
            for i in range(self.fast_period, n):
                fast_val = (fast_val * (self.fast_period - 1) + self.prices[i]) / self.fast_period
            self.curr_fast_smma = fast_val
            self.prev_fast_smma = fast_val

        if n >= self.slow_period:
            slow_val = sum(self.prices[:self.slow_period]) / self.slow_period
            for i in range(self.slow_period, n):
                slow_val = (slow_val * (self.slow_period - 1) + self.prices[i]) / self.slow_period
            self.curr_slow_smma = slow_val
            self.prev_slow_smma = slow_val
        elif n > 0:
            self.curr_slow_smma = sum(self.prices) / n
            self.prev_slow_smma = self.curr_slow_smma

    def update(self, price: float, timestamp: Optional[datetime] = None) -> Tuple[float, float, Optional[CrossoverSignal]]:
        """
        Updates tracker with new tick/bar price. Returns (smma_20, smma_120, optional_crossover_signal).
        """
        self.prices.append(price)
        n = len(self.prices)

        if n < self.fast_period:
            return 0.0, 0.0, None

        # Update Fast SMMA (20)
        if n == self.fast_period:
            self.curr_fast_smma = sum(self.prices) / self.fast_period
        else:
            self.curr_fast_smma = (self.curr_fast_smma * (self.fast_period - 1) + price) / self.fast_period

        # Update Slow SMMA (120)
        if n < self.slow_period:
            self.curr_slow_smma = sum(self.prices) / n  # Warmup approximation before 120
        elif n == self.slow_period:
            self.curr_slow_smma = sum(self.prices[:self.slow_period]) / self.slow_period
        else:
            self.curr_slow_smma = (self.curr_slow_smma * (self.slow_period - 1) + price) / self.slow_period

        # Crossover Detection Logic
        signal: Optional[CrossoverSignal] = None
        curr_time = timestamp or datetime.now()

        # Bullish Crossover: Fast SMMA crosses ABOVE Slow SMMA
        if self.prev_fast_smma <= self.prev_slow_smma and self.curr_fast_smma > self.curr_slow_smma:
            signal = CrossoverSignal(
                symbol=self.symbol,
                crossover_type=CrossoverType.BUY,
                smma_20=self.curr_fast_smma,
                smma_120=self.curr_slow_smma,
                ltp=price,
                timestamp=curr_time
            )
        # Bearish Crossover: Fast SMMA crosses BELOW Slow SMMA
        elif self.prev_fast_smma >= self.prev_slow_smma and self.curr_fast_smma < self.curr_slow_smma:
            signal = CrossoverSignal(
                symbol=self.symbol,
                crossover_type=CrossoverType.SELL,
                smma_20=self.curr_fast_smma,
                smma_120=self.curr_slow_smma,
                ltp=price,
                timestamp=curr_time
            )

        # Shift previous values
        self.prev_fast_smma = self.curr_fast_smma
        self.prev_slow_smma = self.curr_slow_smma

        return self.curr_fast_smma, self.curr_slow_smma, signal
