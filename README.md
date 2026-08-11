# Real-Time Stock Market Screening & AI/ML Analysis System

An enterprise-grade Python application built for real-time NSE stock screening, technical analysis (**SMMA 20 / SMMA 120**), live order book depth evaluation, volume/price metrics, and AI/ML-driven crossover signal classification with human-interpretable trade reasoning.

---

## 📋 Features & Assessment Requirements Checklist

| Requirement | Implementation Detail | Status |
| :--- | :--- | :---: |
| **1. Stock Screening** | Scans all NSE stocks with Last Traded Price (LTP) between **₹30 and ₹500**. | ✅ |
| **2. Liquidity Filter** | Filters screened stocks where both **Bid Quantity > 10,00,000** AND **Ask Quantity > 10,00,000**. | ✅ |
| **3. Technical Indicators** | Real-time incremental **SMMA (20)** and **SMMA (120)** calculation engine with crossover detection. | ✅ |
| **4. Exchange Traded Qty** | Rolling executed quantity calculated for **Last 5 minutes**, **Last 20 minutes**, and **Last 60 minutes**. | ✅ |
| **5. Average Price** | Rolling average LTP calculated over **Last 20 minutes** and **Last 60 minutes**. | ✅ |
| **6. Market Depth** | Top 5 Bids (Price, Quantity, Orders) and Asks, plus total depth volume inspectable per stock. | ✅ |
| **7. Real-Time Dashboard** | PyQt6 modern desktop UI with auto-refreshing table, status badges, and signal popups. | ✅ |
| **8. AI/ML Analysis Engine** | Random Forest model + Explainable AI (XAI) rule engine predicting **Win Probability (%)** and **ACCEPT / AVOID** decisions with natural language explanations. | ✅ |
| **9. Credentials Security** | Auto-masking utility (`mask_credential()`) preventing accidental credential leakage. | ✅ |
| **10. Executable (.exe)** | Automated `build_exe.py` script compiling application into standalone `dist/StockScreenerAI.exe`. | ✅ |

---

## 🏗️ Architecture & Project Structure

```
stock_screener_app/
├── config.py             # System parameters, LTP/Liquidity rules, credentials masking
├── main.py               # Application launcher script
├── build_exe.py          # PyInstaller packaging script
├── requirements.txt      # Python dependencies
├── core/
│   ├── data_models.py    # Dataclasses (TickData, MarketDepth, StockMetrics, AIPrediction)
│   ├── indicators.py     # Incremental SMMA 20 & 120 math & crossover detector
│   └── screener.py       # Stock screening, liquidity filter, and rolling metric windows
├── brokers/
│   ├── base_broker.py    # Abstract base broker interface
│   ├── angel_one.py      # Angel One SmartAPI connector wrapper
│   ├── fyers.py          # Fyers API v3 connector wrapper
│   └── simulator.py      # High-fidelity live market tick simulator (for offline/demo)
├── ai/
│   └── crossover_ml.py   # ML Random Forest model & Explainable AI (XAI) trade inspector
├── gui/
│   └── dashboard.py      # PyQt6 hardware-accelerated desktop GUI dashboard
└── tests/
    ├── test_indicators.py# Unit tests for SMMA & crossover math
    └── test_screener.py  # Unit tests for screening filters & AI predictions
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python main.py
```

### 3. Run Tests
```bash
python -m pytest -q
```

### 4. Build the Executable
```bash
python build_exe.py
```

The compiled executable will be saved at:
`dist/StockScreenerAI.exe`

---

## 🎥 Screen Recording & Video Submission Guide

When recording your demonstration video:
1. **Launch Program**: Start `python main.py` or double-click `dist/StockScreenerAI.exe`.
2. **Live Screening Demo**: Point out how stocks whose LTP is between ₹30 and ₹500 and whose Bid/Ask quantities exceed 10,00,000 are highlighted as **PASSED**, while others are flagged as **PRICE FILTERED** or **LOW LIQUIDITY**.
3. **Market Depth Inspection**: Double-click any stock row (e.g. `SUZLON` or `YESBANK`) to open the **Market Depth Inspector** showing live top 5 Bids and Asks.
4. **AI Signal & Reasoning**: Show the right-hand **AI Signal Inspector** as live SMMA crossovers occur. Highlight how the AI displays:
   - Signal Type: **BUY** (SMMA 20 > 120) / **SELL** (SMMA 20 < 120)
   - Trade Decision: **ACCEPT** or **AVOID**
   - Win Probability (%)
   - Human-readable explanation of why the trade was accepted or avoided (e.g., *Order book ask wall resistance*, *Low volume breakout risk*, *SMMA line entanglement*).
5. **Broker Selector**: Demonstrate switching feeds using the top dropdown selector (Simulated Live Feed / Angel One SmartAPI / Fyers API v3).
