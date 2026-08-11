import sys
from typing import Dict, List, Optional
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QIcon, QBrush, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QPushButton,
    QComboBox, QGroupBox, QSplitter, QTextEdit, QDialog, QFormLayout,
    QFrame, QMessageBox, QTabWidget, QStatusBar
)

import config
from core.data_models import StockMetrics, TickData, CrossoverSignal, CrossoverType, AIPrediction, SignalDecision
from core.screener import StockScreenerEngine
from ai.crossover_ml import SMMACrossoverMLEngine
from brokers.simulator import LiveMarketSimulator
from brokers.angel_one import AngelOneBroker
from brokers.fyers import FyersBroker


class SignalEmitter(QObject):
    tick_received = pyqtSignal(object)
    crossover_detected = pyqtSignal(object, object)


class MarketDepthDialog(QDialog):
    """Popup Dialog to view 5-Level Live Market Depth for a selected stock."""
    def __init__(self, metrics: StockMetrics, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Market Depth - {metrics.symbol}")
        self.setMinimumSize(520, 360)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            QLabel { font-size: 13px; }
            QTableWidget { background-color: #181825; border: 1px solid #313244; color: #cdd6f4; gridline-color: #313244; }
            QHeaderView::section { background-color: #313244; color: #cdd6f4; font-weight: bold; padding: 4px; }
        """)

        layout = QVBoxLayout()
        
        # Summary Header
        header = QLabel(f"<b>{metrics.symbol}</b> | LTP: <b>₹{metrics.ltp:.2f}</b> | "
                        f"Total Bids: <font color='#a6e3a1'>{metrics.total_bid_qty:,}</font> | "
                        f"Total Asks: <font color='#f38ba8'>{metrics.total_ask_qty:,}</font>")
        header.setStyleSheet("font-size: 14px; margin-bottom: 8px;")
        layout.addWidget(header)

        # Depth Table
        depth_table = QTableWidget(5, 6)
        depth_table.setHorizontalHeaderLabels(["Orders", "Bid Qty", "Bid Price", "Ask Price", "Ask Qty", "Orders"])
        depth_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        depth = metrics.market_depth
        for i in range(5):
            # Bids
            if i < len(depth.bids):
                b = depth.bids[i]
                depth_table.setItem(i, 0, QTableWidgetItem(str(b.orders)))
                depth_table.setItem(i, 1, QTableWidgetItem(f"{b.quantity:,}"))
                p_item = QTableWidgetItem(f"₹{b.price:.2f}")
                p_item.setForeground(QBrush(QColor("#a6e3a1")))
                depth_table.setItem(i, 2, p_item)

            
            if i < len(depth.asks):
                a = depth.asks[i]
                p_item2 = QTableWidgetItem(f"₹{a.price:.2f}")
                p_item2.setForeground(QBrush(QColor("#f38ba8")))
                depth_table.setItem(i, 3, p_item2)
                depth_table.setItem(i, 4, QTableWidgetItem(f"{a.quantity:,}"))
                depth_table.setItem(i, 5, QTableWidgetItem(str(a.orders)))

        layout.addWidget(depth_table)
        
        close_btn = QPushButton("Close Inspector")
        close_btn.setStyleSheet("background-color: #45475a; color: white; padding: 6px; border-radius: 4px;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NSE Real-Time Stock Screener & AI Crossover Analysis System")
        self.resize(1380, 850)

        
        self.screener = StockScreenerEngine()
        self.ai_engine = SMMACrossoverMLEngine()
        self.broker = None

        
        self.symbol_row_map: Dict[str, int] = {}
        self.ai_predictions: Dict[str, AIPrediction] = {}

        
        self.emitter = SignalEmitter()
        self.emitter.tick_received.connect(self.handle_tick_update)
        self.emitter.crossover_detected.connect(self.handle_crossover_signal)

        self._setup_ui()
        self._apply_theme()
        self.start_broker_simulator()

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)

        
        control_bar = QHBoxLayout()
        
        title_label = QLabel("⚡ NSE Live Stock Screener & AI Indicator Engine")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #89b4fa;")
        control_bar.addWidget(title_label)

        control_bar.addStretch()

        control_bar.addWidget(QLabel("Broker Feed Source:"))
        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["Simulated Live Feed (NSE)", "Angel One SmartAPI", "Fyers API v3"])
        self.broker_combo.currentIndexChanged.connect(self.on_broker_change)
        control_bar.addWidget(self.broker_combo)

        self.toggle_btn = QPushButton("Pause Stream")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(self.toggle_stream)
        control_bar.addWidget(self.toggle_btn)

        main_layout.addLayout(control_bar)

        
        splitter = QSplitter(Qt.Orientation.Horizontal)

    
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        
        self.filter_summary = QLabel("Criteria: LTP ₹30-₹500 | Liquidity > 10,00,000 Bid & Ask Qty | SMMA(20) & SMMA(120)")
        self.filter_summary.setStyleSheet("background-color: #313244; color: #a6adc8; padding: 6px 12px; border-radius: 4px; font-size: 12px;")
        table_layout.addWidget(self.filter_summary)

        
        self.table = QTableWidget(0, 14)
        columns = [
            "Symbol", "LTP (₹)", "Bid Qty", "Ask Qty", "SMMA (20)", "SMMA (120)",
            "5m Vol", "20m Vol", "60m Vol", "20m Avg LTP", "60m Avg LTP",
            "Screening", "AI Signal", "Win Prob (%)"
        ]
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_market_depth_dialog)
        table_layout.addWidget(self.table)

        splitter.addWidget(table_container)

        
        ai_container = QWidget()
        ai_layout = QVBoxLayout(ai_container)
        ai_layout.setContentsMargins(0, 0, 0, 0)

        ai_header = QLabel("🤖 AI/ML Signal & Trade Reason Inspector")
        ai_header.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        ai_header.setStyleSheet("color: #f9e2af; padding-bottom: 4px;")
        ai_layout.addWidget(ai_header)

        self.ai_log_box = QTextEdit()
        self.ai_log_box.setReadOnly(True)
        self.ai_log_box.setPlaceholderText("Live SMMA crossovers and AI decision reasoning will appear here automatically...")
        ai_layout.addWidget(self.ai_log_box)

        
        inspect_depth_btn = QPushButton("🔍 Inspect Selected Stock Market Depth")
        inspect_depth_btn.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        inspect_depth_btn.clicked.connect(self.open_selected_depth)
        ai_layout.addWidget(inspect_depth_btn)

        splitter.addWidget(ai_container)
        splitter.setSizes([950, 430])

        main_layout.addWidget(splitter)

        
        self.statusBar().showMessage("System Ready. Connected to Live Simulator.")

    def _apply_theme(self):
        """Apply modern Catppuccin Mocha dark design aesthetics."""
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; color: #cdd6f4; }
            QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            QTableWidget {
                background-color: #181825;
                border: 1px solid #313244;
                color: #cdd6f4;
                gridline-color: #313244;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #45475a;
            }
            QTextEdit {
                background-color: #181825;
                border: 1px solid #313244;
                color: #cdd6f4;
                border-radius: 6px;
                font-size: 13px;
            }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45475a; }
            QPushButton:checked { background-color: #f38ba8; color: #11111b; }
        """)

    def start_broker_simulator(self):
        """Initialize and start the live simulator feed."""
        if self.broker:
            self.broker.disconnect()

        self.broker = LiveMarketSimulator(update_interval_sec=0.4)
        
        # Seed historical data for all stocks
        for sym, state in self.broker.stock_states.items():
            hist_prices = self.broker.fetch_historical_prices(sym, limit=150)
            self.screener.register_symbol(sym, initial_prices=hist_prices)

        self.broker.add_tick_callback(lambda tick: self.emitter.tick_received.emit(tick))
        self.broker.connect()
        self.statusBar().showMessage("Streaming real-time ticks from Live Simulator...")

    def on_broker_change(self, index: int):
        broker_name = self.broker_combo.currentText()
        if "Simulated" in broker_name:
            self.start_broker_simulator()
        else:
            QMessageBox.information(
                self, "Broker Configuration",
                f"Configured for {broker_name}.\nCredentials loaded securely from config.py / Env Variables.\n"
                f"Switching feed listener..."
            )
            if broker_name == "Angel One SmartAPI":
                self.broker = AngelOneBroker()
            else:
                self.broker = FyersBroker()
            self.broker.connect()

    def toggle_stream(self):
        if self.toggle_btn.isChecked():
            self.toggle_btn.setText("Resume Stream")
            if self.broker:
                self.broker.disconnect()
            self.statusBar().showMessage("Stream Paused.")
        else:
            self.toggle_btn.setText("Pause Stream")
            if self.broker:
                self.broker.connect()
            self.statusBar().showMessage("Stream Resumed.")

    def handle_tick_update(self, tick: TickData):
        """Thread-safe handler invoked whenever a new market tick arrives."""
        metrics, signal = self.screener.process_tick(tick)
        
        if signal and signal.crossover_type != CrossoverType.NONE:
            ai_pred = self.ai_engine.evaluate_crossover(signal, metrics)
            self.ai_predictions[metrics.symbol] = ai_pred
            self.emitter.crossover_detected.emit(signal, ai_pred)

        self._update_table_row(metrics)

    def handle_crossover_signal(self, signal: CrossoverSignal, ai_pred: AIPrediction):
        """Append crossover signal and AI decision reasoning to the inspector drawer."""
        timestamp_str = signal.timestamp.strftime("%H:%M:%S")
        is_buy = signal.crossover_type == CrossoverType.BUY
        
        sig_color = "#a6e3a1" if is_buy else "#f38ba8"
        dec_color = "#a6e3a1" if ai_pred.decision == SignalDecision.ACCEPT else "#f38ba8"

        log_html = f"""
        <div style='margin-bottom: 12px; border-left: 4px solid {dec_color}; padding-left: 8px;'>
            <b>[{timestamp_str}] {signal.symbol}</b> — 
            <font color='{sig_color}'><b>SMMA {signal.crossover_type.value} CROSSOVER</b></font><br/>
            LTP: <b>₹{signal.ltp:.2f}</b> | SMMA(20): ₹{signal.smma_20:.2f} | SMMA(120): ₹{signal.smma_120:.2f}<br/>
            AI Trade Decision: <font color='{dec_color}'><b>{ai_pred.decision.value}</b></font> 
            (Win Probability: <b>{ai_pred.win_probability:.1f}%</b>)<br/>
            <b>Market Conditions & AI Observations:</b>
            <ul style='margin-top: 4px; margin-bottom: 4px;'>
        """
        for reason in ai_pred.reasons:
            log_html += f"<li>{reason}</li>"
        log_html += "</ul></div><hr style='border: 1px solid #313244;'/>"

        self.ai_log_box.append(log_html)

    def _update_table_row(self, metrics: StockMetrics):
        symbol = metrics.symbol
        
        if symbol not in self.symbol_row_map:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.symbol_row_map[symbol] = row
        else:
            row = self.symbol_row_map[symbol]

        # Formatting values
        ai_pred = self.ai_predictions.get(symbol)

        items = [
            (symbol, "#cdd6f4", True),
            (f"₹{metrics.ltp:.2f}", "#cdd6f4", False),
            (f"{metrics.total_bid_qty:,}", "#a6e3a1" if metrics.total_bid_qty >= config.LIQUIDITY_BID_MIN else "#f38ba8", False),
            (f"{metrics.total_ask_qty:,}", "#a6e3a1" if metrics.total_ask_qty >= config.LIQUIDITY_ASK_MIN else "#f38ba8", False),
            (f"₹{metrics.smma_20:.2f}" if metrics.smma_20 > 0 else "N/A", "#89b4fa", False),
            (f"₹{metrics.smma_120:.2f}" if metrics.smma_120 > 0 else "N/A", "#cba6f7", False),
            (f"{metrics.vol_5m:,}", "#cdd6f4", False),
            (f"{metrics.vol_20m:,}", "#cdd6f4", False),
            (f"{metrics.vol_60m:,}", "#cdd6f4", False),
            (f"₹{metrics.avg_price_20m:.2f}", "#cdd6f4", False),
            (f"₹{metrics.avg_price_60m:.2f}", "#cdd6f4", False),
            ("PASSED" if metrics.passes_all_filters else ("PRICE FILTERED" if not metrics.passes_ltp_filter else "LOW LIQUIDITY"), 
             "#a6e3a1" if metrics.passes_all_filters else "#f38ba8", True),
            (ai_pred.crossover_type.value if ai_pred else "NONE", "#a6e3a1" if ai_pred and ai_pred.crossover_type == CrossoverType.BUY else ("#f38ba8" if ai_pred and ai_pred.crossover_type == CrossoverType.SELL else "#a6adc8"), True),
            (f"{ai_pred.win_probability:.1f}% ({ai_pred.decision.value})" if ai_pred else "N/A", 
             "#a6e3a1" if ai_pred and ai_pred.decision == SignalDecision.ACCEPT else ("#f38ba8" if ai_pred else "#a6adc8"), True)
        ]

        for col_idx, (text, color_hex, is_bold) in enumerate(items):
            item = QTableWidgetItem(text)
            item.setForeground(QBrush(QColor(color_hex)))
            if is_bold:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.table.setItem(row, col_idx, item)

    def open_market_depth_dialog(self, index):
        row = index.row()
        symbol_item = self.table.item(row, 0)
        if symbol_item:
            symbol = symbol_item.text()
            metrics = self.screener.latest_metrics.get(symbol)
            if metrics:
                dialog = MarketDepthDialog(metrics, self)
                dialog.exec()

    def open_selected_depth(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            self.open_market_depth_dialog(selected_rows[0])
        else:
            QMessageBox.information(self, "Market Depth", "Please select a stock row in the table first.")

    def closeEvent(self, event):
        if self.broker:
            self.broker.disconnect()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
