import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import backtrader as bt
import ta # Technical Analysis

# STEP 1: Getting and Processing Stock Data
def get_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    stock_data.fillna(method='ffill', inplace=True)
    return stock_data

# STEP 2: Calculate Technical Indicators
def calculate_indicators(data):
    data['MACD'] = ta.trend.macd(data['Close'])
    data['MACD_Signal'] = ta.trend.macd_signal(data['Close'])
    data['RSI'] = ta.momentum.rsi(data['Close'])
    return data

# STEP 3: Generate Buy/Sell Signals
def generate_signals(data):
    data['Buy_Signal'] = ((data['MACD'] > data['MACD_Signal']) & 
                          (data['MACD'].shift(1) <= data['MACD_Signal'].shift(1))).astype(int)
    data['Sell_Signal'] = ((data['MACD'] < data['MACD_Signal']) & 
                           (data['MACD'].shift(1) >= data['MACD_Signal'].shift(1))).astype(int)
    return data

# STEP 4: Visualization
def plot_signals(data):
    plt.figure(figsize=(14, 7))
    plt.plot(data['Close'], label='Close Price', alpha=0.5)
    plt.plot(data['MACD'], label='MACD', color='red', alpha=0.5)
    plt.plot(data['MACD_Signal'], label='Signal Line', color='blue', alpha=0.5)
    plt.scatter(data.index, data['Close'].where(data['Buy_Signal'] == 1), label='Buy Signal', marker='^', color='green', alpha=1)
    plt.scatter(data.index, data['Close'].where(data['Sell_Signal'] == 1), label='Sell Signal', marker='v', color='red', alpha=1)
    plt.title('Stock Price with Buy and Sell Signals')
    plt.legend()
    plt.show()

# Main execution
if __name__ == "__main__":
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2023-01-01"
    
    # Get and process data
    data = get_stock_data(ticker, start_date, end_date)
    print("Fetched Data:")
    print(data.head())
    
    # Calculate indicators and generate signals
    data = calculate_indicators(data)
    data = generate_signals(data)
    
    # Display results
    print("\nTechnical Indicators and Signals:")
    print(data[['Close', 'MACD', 'MACD_Signal', 'RSI', 'Buy_Signal', 'Sell_Signal']].tail())
    
    # Plot results
    plot_signals(data)
    
    # Save data to CSV
    data.to_csv('aapl_historical_data.csv')
    print("\nData saved to aapl_historical_data.csv")


# Function for the trading algorithm
def implement_trading_strategy(data, initial_capital=10000):
    data['Position'] = 0  # 1 for long, -1 for short, 0 for neutral
    data['Trade'] = 0  # 1 for buy, -1 for sell
    data['Portfolio'] = initial_capital

    position = 0
    for i in range(1, len(data)):
        if data['Buy_Signal'].iloc[i] == 1 and position == 0:
            position = 1
            data['Position'].iloc[i] = 1
            data['Trade'].iloc[i] = 1
        elif data['Sell_Signal'].iloc[i] == 1 and position == 1:
            position = 0
            data['Position'].iloc[i] = 0
            data['Trade'].iloc[i] = -1
        else:
            data['Position'].iloc[i] = position

        if data['Trade'].iloc[i] == 1:
            shares_bought = data['Portfolio'].iloc[i-1] // data['Close'].iloc[i]
            data['Portfolio'].iloc[i] = data['Portfolio'].iloc[i-1] - (shares_bought * data['Close'].iloc[i])
        elif data['Trade'].iloc[i] == -1:
            shares_sold = data['Portfolio'].iloc[i-1] // data['Close'].iloc[i-1]
            data['Portfolio'].iloc[i] = data['Portfolio'].iloc[i-1] + (shares_sold * data['Close'].iloc[i])
        else:
            if position == 1:
                data['Portfolio'].iloc[i] = data['Portfolio'].iloc[i-1] * (data['Close'].iloc[i] / data['Close'].iloc[i-1])
            else:
                data['Portfolio'].iloc[i] = data['Portfolio'].iloc[i-1]

    return data

"""The trading algorithm works as follows:

It starts with an initial capital (default $10,000).
When a buy signal is generated, it invests all available capital in the stock.
When a sell signal is generated, it sells all shares.
The portfolio value is updated daily based on the position and stock price.

This is a basic implementation and doesn't account for factors like transaction costs,
 slippage, or fractional shares. In a real-world scenario, you'd want to include these 
 factors and potentially add more sophisticated risk management techniques"""

# Function to calculate and print strategy performance
def print_strategy_performance(data, initial_capital):
    total_return = (data['Portfolio'].iloc[-1] - initial_capital) / initial_capital * 100
    buy_hold_return = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
    
    print(f"Strategy Total Return: {total_return:.2f}%")
    print(f"Buy and Hold Return: {buy_hold_return:.2f}%")

# Update the main execution block
if __name__ == "__main__":
    ticker = "AAPL"
    start_date = "2020-01-01"
    end_date = "2023-01-01"
    initial_capital = 10000
    
    # Get and process data
    data = get_stock_data(ticker, start_date, end_date)
    print("Fetched Data:")
    print(data.head())
    
    # Calculate indicators and generate signals
    data = calculate_indicators(data)
    data = generate_signals(data)
    
    # Implement trading strategy
    data = implement_trading_strategy(data, initial_capital)
    
    # Display results
    print("\nTechnical Indicators and Signals:")
    print(data[['Close', 'MACD', 'MACD_Signal', 'RSI', 'Buy_Signal', 'Sell_Signal', 'Portfolio']].tail())
    
    # Print strategy performance
    print("\nStrategy Performance:")
    print_strategy_performance(data, initial_capital)
    
    # Plot results
    plot_signals(data)
    
    # Save data to CSV
    data.to_csv('aapl_historical_data.csv')
    print("\nData saved to aapl_historical_data.csv")