import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image

def get_stock_data(ticker, start_date, end_date):
    try:
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        stock_data.fillna(method='ffill', inplace=True)
        return stock_data[['Open', 'High', 'Low', 'Close']]
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

def implement_trading_strategy(data, initial_capital):
    df = data.copy()
    df['Position'] = 0
    df['Trade'] = 0
    df['Portfolio'] = float(initial_capital)
    df['Shares'] = 0
    df['Cash'] = float(initial_capital)

    position = 0
    for i in range(1, len(df)):
        if df['Buy_Signal'].iloc[i] == 1 and position == 0:
            position = 1
            df.loc[df.index[i], 'Position'] = 1
            df.loc[df.index[i], 'Trade'] = 1
            shares_bought = df['Cash'].iloc[i-1] // df['Close'].iloc[i]
            df.loc[df.index[i], 'Shares'] = shares_bought
            df.loc[df.index[i], 'Cash'] = df['Cash'].iloc[i-1] - (shares_bought * df['Close'].iloc[i])
        elif df['Sell_Signal'].iloc[i] == 1 and position == 1:
            position = 0
            df.loc[df.index[i], 'Position'] = 0
            df.loc[df.index[i], 'Trade'] = -1
            df.loc[df.index[i], 'Cash'] = df['Cash'].iloc[i-1] + (df['Shares'].iloc[i-1] * df['Close'].iloc[i])
            df.loc[df.index[i], 'Shares'] = 0
        else:
            df.loc[df.index[i], 'Position'] = position
            df.loc[df.index[i], 'Shares'] = df['Shares'].iloc[i-1]
            df.loc[df.index[i], 'Cash'] = df['Cash'].iloc[i-1]

        df.loc[df.index[i], 'Portfolio'] = df['Cash'].iloc[i] + (df['Shares'].iloc[i] * df['Close'].iloc[i])

    return df
def plot_stock_data(data, ticker, initial_investment):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, 
                        subplot_titles=(f'{ticker} Stock Price', 'MACD'),
                        specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

    # Plot stock price as candlesticks
    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'],
                                 name='Price'),
                  row=1, col=1, secondary_y=False)

    # Add initial investment line on secondary y-axis
    fig.add_trace(go.Scatter(x=data.index, y=[initial_investment]*len(data), 
                             name='Initial Investment', 
                             line=dict(color='green', dash='dash')), 
                  row=1, col=1, secondary_y=True)

    # Add buy and sell signals
    fig.add_trace(go.Scatter(x=data[data['Buy_Signal'] == 1].index, 
                             y=data[data['Buy_Signal'] == 1]['Low'],
                             mode='markers', 
                             name='Buy Signal', 
                             marker=dict(color='green', symbol='triangle-up', size=10)),
                  row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=data[data['Sell_Signal'] == 1].index, 
                             y=data[data['Sell_Signal'] == 1]['High'],
                             mode='markers', 
                             name='Sell Signal', 
                             marker=dict(color='red', symbol='triangle-down', size=10)),
                  row=1, col=1, secondary_y=False)

    # Plot MACD with colors
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal Line', line=dict(color='red')), row=2, col=1)

    # Update layout
    fig.update_layout(height=800, width=1000, title_text=f"{ticker} Stock Analysis")
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])  # Hide weekends
    fig.update_yaxes(title_text="Price ($)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Investment ($)", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="MACD", row=2, col=1)

    # Update the range of the price axis
    price_range = data['Close'].max() - data['Close'].min()
    fig.update_yaxes(range=[data['Close'].min() - price_range*0.1, data['Close'].max() + price_range*0.1], row=1, col=1, secondary_y=False)

    return fig

def main():
    st.title('Stock Trading Dashboard')

    # Sidebar
    st.sidebar.header('User Input')
    tickers = st.sidebar.text_input('Enter stock tickers (comma-separated)', 'AAPL,GOOGL,MSFT').split(',')
    start_date = st.sidebar.date_input('Start Date', pd.to_datetime('2020-01-01'))
    end_date = st.sidebar.date_input('End Date', pd.to_datetime('2023-01-01'))
    
    initial_investment = st.sidebar.number_input('Initial Investment ($)', min_value=1000, max_value=1000000, value=10000, step=1000)

    # Add "Made By" section to sidebar with icon buttons
    st.sidebar.header('Made By:')
    col1, col2, col3 = st.sidebar.columns(3)

    if col1.button('GitHub', key='github'):
        st.sidebar.markdown("[GitHub](https://github.com/yourusername)")
    
    if col2.button('Portfolio', key='portfolio'):
        st.sidebar.markdown("[Portfolio](https://yourportfolio.com)")
    
    if col3.button('LinkedIn', key='linkedin'):
        st.sidebar.markdown("[LinkedIn](https://www.linkedin.com/in/yourprofile)")

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
            data = implement_trading_strategy(data, initial_capital=initial_investment)

            fig = plot_stock_data(data, ticker, initial_investment)
            st.plotly_chart(fig)

            # Display strategy performance
            buy_hold_return = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
            final_portfolio_value = data['Portfolio'].iloc[-1]
            total_return = ((final_portfolio_value - initial_investment) / initial_investment) * 100
            
            st.subheader('Strategy Performance')
            col1, col2, col3 = st.columns(3)
            col1.metric("Initial Investment", f"${initial_investment:,.2f}")
            col2.metric("Strategy Total Return", f"{total_return:.2f}%")
            col3.metric("Buy and Hold Return", f"{buy_hold_return:.2f}%")

            # Display recent data
            st.subheader('Recent Data')
            st.dataframe(data[['Close', 'MACD', 'MACD_Signal', 'RSI', 'Buy_Signal', 'Sell_Signal', 'Portfolio']].tail())

            # Display current position
            current_position = "Holding" if data['Position'].iloc[-1] == 1 else "Not Holding"
            st.info(f"Current Position: {current_position}")

if __name__ == '__main__':
    main()