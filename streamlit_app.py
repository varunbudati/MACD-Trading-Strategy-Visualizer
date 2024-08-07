import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_stock_data(ticker, start_date, end_date):
    try:
        # Disable progress bar
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        stock_data.fillna(method='ffill', inplace=True)
        return stock_data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return pd.DataFrame() 

def calculate_indicators(data):
    data['MACD'] = ta.trend.macd(data['Close'])
    data['MACD_Signal'] = ta.trend.macd_signal(data['Close'])
    data['RSI'] = ta.momentum.rsi(data['Close'])
    return data

def generate_signals(data):
    data['Buy_Signal'] = ((data['MACD'] > data['MACD_Signal']) & 
                          (data['MACD'].shift(1) <= data['MACD_Signal'].shift(1))).astype(int)
    data['Sell_Signal'] = ((data['MACD'] < data['MACD_Signal']) & 
                           (data['MACD'].shift(1) >= data['MACD_Signal'].shift(1))).astype(int)
    return data

def implement_trading_strategy(data, initial_capital=10000.0):
    df = data.copy()
    df['Position'] = 0
    df['Trade'] = 0
    df['Portfolio'] = float(initial_capital)

    position = 0
    for i in range(1, len(df)):
        if df['Buy_Signal'].iloc[i] == 1 and position == 0:
            position = 1
            df.loc[df.index[i], 'Position'] = 1
            df.loc[df.index[i], 'Trade'] = 1
        elif df['Sell_Signal'].iloc[i] == 1 and position == 1:
            position = 0
            df.loc[df.index[i], 'Position'] = 0
            df.loc[df.index[i], 'Trade'] = -1
        else:
            df.loc[df.index[i], 'Position'] = position

        if df['Trade'].iloc[i] == 1:
            shares_bought = df['Portfolio'].iloc[i-1] // df['Close'].iloc[i]
            df.loc[df.index[i], 'Portfolio'] = df['Portfolio'].iloc[i-1] - (shares_bought * df['Close'].iloc[i])
        elif df['Trade'].iloc[i] == -1:
            shares_sold = df['Portfolio'].iloc[i-1] // df['Close'].iloc[i-1]
            df.loc[df.index[i], 'Portfolio'] = df['Portfolio'].iloc[i-1] + (shares_sold * df['Close'].iloc[i])
        else:
            if position == 1:
                df.loc[df.index[i], 'Portfolio'] = df['Portfolio'].iloc[i-1] * (df['Close'].iloc[i] / df['Close'].iloc[i-1])
            else:
                df.loc[df.index[i], 'Portfolio'] = df['Portfolio'].iloc[i-1]

    return df

def plot_stock_data(data, ticker):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=(f'{ticker} Stock Price', 'MACD'))

    # Plot stock price
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Buy_Signal'] == 1].index, y=data[data['Buy_Signal'] == 1]['Close'], 
                             mode='markers', name='Buy Signal', marker=dict(color='green', symbol='triangle-up', size=10)), row=1, col=1)
    fig.add_trace(go.Scatter(x=data[data['Sell_Signal'] == 1].index, y=data[data['Sell_Signal'] == 1]['Close'], 
                             mode='markers', name='Sell Signal', marker=dict(color='red', symbol='triangle-down', size=10)), row=1, col=1)

    # Plot MACD
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal Line'), row=2, col=1)

    fig.update_layout(height=600, width=800, title_text=f"{ticker} Stock Analysis")
    return fig

def main():
    st.sidebar.header('User Input')
    tickers = st.sidebar.text_input('Enter stock tickers (comma-separated)', 'AAPL,GOOGL,MSFT').split(',')
    start_date = st.sidebar.date_input('Start Date', pd.to_datetime('2020-01-01'))
    end_date = st.sidebar.date_input('End Date', pd.to_datetime('2023-01-01'))

    if st.sidebar.button('Analyze Stocks'):
        for ticker in tickers:
            ticker = ticker.strip().upper()
            st.header(f'Analysis for {ticker}')

            data = get_stock_data(ticker, start_date, end_date)
            
            if data.empty:
                st.warning(f"No data available for {ticker}. Skipping analysis.")
                continue

            data = calculate_indicators(data)
            data = generate_signals(data)
            data = implement_trading_strategy(data)

            fig = plot_stock_data(data, ticker)
            st.plotly_chart(fig)

            # Display strategy performance
            initial_capital = 10000
            total_return = (data['Portfolio'].iloc[-1] - initial_capital) / initial_capital * 100
            buy_hold_return = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
            
            st.subheader('Strategy Performance')
            col1, col2 = st.columns(2)
            col1.metric("Strategy Total Return", f"{total_return:.2f}%")
            col2.metric("Buy and Hold Return", f"{buy_hold_return:.2f}%")

            # Display recent data
            st.subheader('Recent Data')
            st.dataframe(data[['Close', 'MACD', 'MACD_Signal', 'RSI', 'Buy_Signal', 'Sell_Signal', 'Portfolio']].tail())

if __name__ == '__main__':
    main()