"""
Main entry point for the AI/ML-Based Stock Market Screening and Analysis System.
Launches the PyQt6 Desktop GUI Dashboard.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.dashboard import main

if __name__ == "__main__":
    main()
