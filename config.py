"""
System Configuration & Constants for Stock Market Screening & Analysis System.
Contains broker credentials structure, indicator parameters, and screening rules.
"""

import os

# Screening Parameters
LTP_MIN: float = 30.0
LTP_MAX: float = 500.0

LIQUIDITY_BID_MIN: int = 1_000_000  # 10 Lakhs (10,00,000)
LIQUIDITY_ASK_MIN: int = 1_000_000  # 10 Lakhs (10,00,000)

# Technical Indicator Parameters
SMMA_FAST_PERIOD: int = 20
SMMA_SLOW_PERIOD: int = 120

# Time Windows (in minutes)
WINDOW_5M: int = 5
WINDOW_20M: int = 20
WINDOW_60M: int = 60

# Default Sample NSE Universe (High Liquidity Stocks + Screening Candidates)
DEFAULT_NSE_UNIVERSE = [
    "RELIANCE", "TATAMOTORS", "SBIN", "YESBANK", "SUZLON",
    "IDEA", "IDFCFIRSTB", "NHPC", "IRFC", "PNB", "SJVN",
    "HUDCO", "IOC", "GAIL", "ZOMATO", "TATASTEEL", "BHEL",
    "GMRINFRA", "RENUKA", "TRIDENT", "NBCC", "SOUTHBANK"
]

# Masking Utility for Security Compliance
def mask_credential(cred: str, visible_chars: int = 4) -> str:
    """Mask credentials for video recording / code submission safety."""
    if not cred or len(cred) <= visible_chars:
        return "****"
    return cred[:visible_chars] + "*" * (len(cred) - visible_chars)

# Broker Credentials (Can be loaded from env or user input dialog)
ANGEL_ONE_CONFIG = {
    "api_key": os.getenv("ANGEL_API_KEY", "MOCKED_ANGEL_KEY_12345"),
    "client_code": os.getenv("ANGEL_CLIENT_CODE", "MOCKED_USER"),
    "password": os.getenv("ANGEL_PASSWORD", "MOCKED_PASS"),
    "totp_key": os.getenv("ANGEL_TOTP_KEY", "MOCKED_TOTP")
}

FYERS_CONFIG = {
    "client_id": os.getenv("FYERS_CLIENT_ID", "MOCKED_FYERS_ID"),
    "access_token": os.getenv("FYERS_ACCESS_TOKEN", "MOCKED_ACCESS_TOKEN")
}
