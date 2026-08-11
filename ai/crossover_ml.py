"""
AI/ML Engine for SMMA Crossover Evaluation & Explainable AI (XAI) Signal Filtering.
Evaluates order book imbalance, volume acceleration, indicator divergence, and market micro-structure.
Outputs signal win probability (%) and human-readable trade decision explanations.
"""

import numpy as np

from sklearn.ensemble import RandomForestClassifier
from typing import List, Dict, Tuple
from core.data_models import CrossoverSignal, CrossoverType, StockMetrics, AIPrediction, SignalDecision


class SMMACrossoverMLEngine:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self._is_trained = False
        self._train_synthetic_model()

    def _train_synthetic_model(self):
        """
        Train ML Random Forest classifier on market depth and momentum features.
        Features: [OrderBookImbalance, SMMADivergence, VolAcceleration, SpreadRatio, PriceVsAvg60m]
        Target: 1 (Profitable Trade), 0 (Failing / False Breakout Trade)
        """
        np.random.seed(42)
        n_samples = 1000

        # Generate realistic feature distribution
        ob_imbalance = np.random.uniform(0.3, 3.0, n_samples)
        smma_diff = np.random.uniform(-3.0, 3.0, n_samples)
        vol_accel = np.random.uniform(0.5, 3.0, n_samples)
        spread_ratio = np.random.uniform(0.0001, 0.005, n_samples)
        price_vs_avg = np.random.uniform(-0.05, 0.05, n_samples)

        X = np.column_stack([ob_imbalance, smma_diff, vol_accel, spread_ratio, price_vs_avg])

        # Define ground truth labeling rules representing real market mechanics:
        # High probability if Order Book aligns with crossover direction AND Volume is accelerating AND Spread is tight
        y = []
        for i in range(n_samples):
            is_buy = smma_diff[i] > 0
            imbalance = ob_imbalance[i]
            accel = vol_accel[i]
            spread = spread_ratio[i]

            score = 0.5
            if is_buy and imbalance > 1.2:
                score += 0.25
            elif not is_buy and imbalance < 0.8:
                score += 0.25

            if accel > 1.3:
                score += 0.20
            if spread < 0.002:
                score += 0.10

            y.append(1 if score >= 0.70 else 0)

        self.model.fit(X, y)
        self._is_trained = True

    def extract_features(self, signal: CrossoverSignal, metrics: StockMetrics) -> np.ndarray:
        """Extract ML feature vector from live tick metrics and crossover signal."""
        bid_qty = max(1, metrics.total_bid_qty)
        ask_qty = max(1, metrics.total_ask_qty)
        ob_imbalance = bid_qty / ask_qty

        ltp = max(0.01, metrics.ltp)
        smma_diff_pct = ((metrics.smma_20 - metrics.smma_120) / ltp) * 100.0

        vol_20m_avg_5m = (metrics.vol_20m / 4.0) if metrics.vol_20m > 0 else 1.0
        vol_accel = (metrics.vol_5m / vol_20m_avg_5m) if vol_20m_avg_5m > 0 else 1.0

        top_bid = metrics.market_depth.top_bid_price
        top_ask = metrics.market_depth.top_ask_price
        spread = max(0.01, top_ask - top_bid) if top_ask > top_bid else 0.05
        spread_ratio = spread / ltp

        price_vs_avg60m = ((ltp - metrics.avg_price_60m) / metrics.avg_price_60m) if metrics.avg_price_60m > 0 else 0.0

        return np.array([[ob_imbalance, smma_diff_pct, vol_accel, spread_ratio, price_vs_avg60m]])

    def evaluate_crossover(self, signal: CrossoverSignal, metrics: StockMetrics) -> AIPrediction:
        """
        Evaluate Crossover Signal using ML Probability + Explainable AI (XAI) Rule Inspector.
        """
        features = self.extract_features(signal, metrics)
        ob_imbalance, smma_diff_pct, vol_accel, spread_ratio, price_vs_avg60m = features[0]

        # ML Probability Prediction
        probs = self.model.predict_proba(features)[0]
        win_prob = float(probs[1]) * 100.0 if len(probs) > 1 else 50.0

        reasons: List[str] = []
        is_buy = (signal.crossover_type == CrossoverType.BUY)

        # Explainable AI (XAI) Observation & Reason Generator
        # Rule 1: Order Book Liquidity Imbalance
        if is_buy and ob_imbalance < 1.0:
            reasons.append(f"❌ Ask Quantity ({metrics.total_ask_qty:,}) exceeds Bid Quantity ({metrics.total_bid_qty:,}). Selling pressure wall may cap upside.")
            win_prob -= 15.0
        elif is_buy and ob_imbalance >= 1.3:
            reasons.append(f"✅ Strong Bid Depth Wall ({metrics.total_bid_qty:,} Bids vs {metrics.total_ask_qty:,} Asks). Buyer support confirmed.")
        elif not is_buy and ob_imbalance > 1.0:
            reasons.append(f"❌ Bid Quantity ({metrics.total_bid_qty:,}) exceeds Ask Quantity ({metrics.total_ask_qty:,}). Strong buyer support wall may prevent price drop.")
            win_prob -= 15.0
        elif not is_buy and ob_imbalance <= 0.7:
            reasons.append(f"✅ Heavy Ask Wall ({metrics.total_ask_qty:,} Asks vs {metrics.total_bid_qty:,} Bids) accelerating breakdown momentum.")

        # Rule 2: Volume Acceleration behind Crossover
        if vol_accel < 0.9:
            reasons.append(f"⚠️ Low Volume Breakout: 5-min volume ({metrics.vol_5m:,}) is below 20-min average rate ({int(metrics.vol_20m/4):,}). High risk of false crossover.")
            win_prob -= 12.0
        elif vol_accel > 1.4:
            reasons.append(f"🔥 Volume Expansion: 5-min volume ({metrics.vol_5m:,}) surged {vol_accel:.2f}x above recent average, confirming institutional participation.")

        # Rule 3: SMMA Angle & Distance
        smma_gap = abs(metrics.smma_20 - metrics.smma_120)
        if smma_gap < (metrics.ltp * 0.001):
            reasons.append(f"⚠️ Choppy Sideways Range: SMMA(20) and SMMA(120) lines are entangled (Gap: ₹{smma_gap:.2f}). High whipsaw probability.")
            win_prob -= 18.0

        # Rule 4: Mean-Reversion Over-Extension
        if is_buy and price_vs_avg60m > 0.03:
            reasons.append(f"⚠️ Over-Extended: Current LTP ₹{metrics.ltp:.2f} is {price_vs_avg60m*100:.1f}% above 60-min Avg LTP (₹{metrics.avg_price_60m:.2f}). Risk of pull-back.")
            win_prob -= 10.0
        elif not is_buy and price_vs_avg60m < -0.03:
            reasons.append(f"⚠️ Over-Sold: Current LTP ₹{metrics.ltp:.2f} is {abs(price_vs_avg60m)*100:.1f}% below 60-min Avg LTP (₹{metrics.avg_price_60m:.2f}). Risk of bounce.")
            win_prob -= 10.0

        # Bound probability between 5.0% and 98.0%
        win_prob = max(5.0, min(98.0, win_prob))
        decision = SignalDecision.ACCEPT if win_prob >= 60.0 else SignalDecision.AVOID

        if not reasons:
            if decision == SignalDecision.ACCEPT:
                reasons.append("✅ Market structure, depth liquidity, and momentum align with the trade direction.")
            else:
                reasons.append("❌ Sub-optimal reward-to-risk balance under current market liquidity conditions.")

        return AIPrediction(
            symbol=signal.symbol,
            crossover_type=signal.crossover_type,
            decision=decision,
            win_probability=round(win_prob, 1),
            reasons=reasons,
            metrics_snapshot={
                "ob_imbalance": round(ob_imbalance, 2),
                "vol_accel": round(vol_accel, 2),
                "smma_20": round(metrics.smma_20, 2),
                "smma_120": round(metrics.smma_120, 2)
            }
        )
