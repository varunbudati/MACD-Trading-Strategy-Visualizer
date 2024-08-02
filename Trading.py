import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import backtrader as bt

import backtrader as bt

# Step 1: Download Historical Data
import yfinance as yf
data = yf.download('AAPL', start="2020-01-01", end="2023-01-01")

# Step 2: Define Strategy
class MACDStrategy(bt.Strategy):
    def __init__(self):
        self.macd = bt.indicators.MACD(self.data)
        self.signal_line = bt.indicators.MACD(self.data).signal
        self.crossover = bt.indicators.CrossOver(self.macd, self.signal_line)
        
    def next(self):
        if not self.position:  # Not in the market
            if self.crossover > 0:  # Buy signal
                self.buy()
        elif self.crossover < 0:  # Sell signal
            self.sell()

# Step 3: Backtest Strategy
cerebro = bt.Cerebro()
cerebro.addstrategy(MACDStrategy)
data_feed = bt.feeds.PandasData(dataname=data)
cerebro.adddata(data_feed)
cerebro.run()
cerebro.plot()
