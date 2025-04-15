import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

def get_stock_data(ticker, start_date, end_date):
    # Ensure that start_date is before end_date
    if start_date > end_date:
        st.warning(f"Start date ({start_date}) is after end date ({end_date}). Swapping dates.")
        start_date, end_date = end_date, start_date
    
    try:
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        # Check if we got any data
        if stock_data.empty:
            st.warning(f"No data found for {ticker} between {start_date} and {end_date}")
            return pd.DataFrame()
        
        # Use ffill() instead of deprecated fillna(method='ffill')
        stock_data.ffill(inplace=True)
        return stock_data[['Open', 'High', 'Low', 'Close']]
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return pd.DataFrame()

def calculate_indicators(data):
    # Ensure Close is a 1-dimensional Series
    close_series = data['Close'].squeeze()
    
    # Check if it's properly a Series
    if not isinstance(close_series, pd.Series):
        # If it's not a Series, convert it to one
        close_series = pd.Series(close_series, index=data.index)
    
    # Now calculate the indicators
    data['MACD'] = ta.trend.macd(close_series)
    data['MACD_Signal'] = ta.trend.macd_signal(close_series)
    data['RSI'] = ta.momentum.rsi(close_series)
    
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
            
            # Extract values safely for calculation
            cash_value = df['Cash'].iloc[i-1]
            close_value = df['Close'].iloc[i]
            
            # Convert to float if Series
            if isinstance(cash_value, pd.Series):
                cash_value = float(cash_value.iloc[0])
            if isinstance(close_value, pd.Series):
                close_value = float(close_value.iloc[0])
                
            shares_bought = cash_value // close_value
            df.loc[df.index[i], 'Shares'] = shares_bought
            df.loc[df.index[i], 'Cash'] = cash_value - (shares_bought * close_value)
        elif df['Sell_Signal'].iloc[i] == 1 and position == 1:
            position = 0
            df.loc[df.index[i], 'Position'] = 0
            df.loc[df.index[i], 'Trade'] = -1
            
            # Extract values safely for calculation
            cash_value = df['Cash'].iloc[i-1]
            shares_value = df['Shares'].iloc[i-1]
            close_value = df['Close'].iloc[i]
            
            # Convert to float if Series
            if isinstance(cash_value, pd.Series):
                cash_value = float(cash_value.iloc[0])
            if isinstance(shares_value, pd.Series):
                shares_value = float(shares_value.iloc[0])
            if isinstance(close_value, pd.Series):
                close_value = float(close_value.iloc[0])
                
            df.loc[df.index[i], 'Cash'] = cash_value + (shares_value * close_value)
            df.loc[df.index[i], 'Shares'] = 0
        else:
            df.loc[df.index[i], 'Position'] = position
            
            # Extract values safely
            shares_value = df['Shares'].iloc[i-1]
            cash_value = df['Cash'].iloc[i-1]
            
            # Convert to float if Series
            if isinstance(shares_value, pd.Series):
                shares_value = float(shares_value.iloc[0])
            if isinstance(cash_value, pd.Series):
                cash_value = float(cash_value.iloc[0])
                
            df.loc[df.index[i], 'Shares'] = shares_value
            df.loc[df.index[i], 'Cash'] = cash_value

        # Calculate portfolio value
        cash_value = df['Cash'].iloc[i]
        shares_value = df['Shares'].iloc[i]
        close_value = df['Close'].iloc[i]
        
        # Convert to float if Series
        if isinstance(cash_value, pd.Series):
            cash_value = float(cash_value.iloc[0])
        if isinstance(shares_value, pd.Series):
            shares_value = float(shares_value.iloc[0])
        if isinstance(close_value, pd.Series):
            close_value = float(close_value.iloc[0])
            
        df.loc[df.index[i], 'Portfolio'] = cash_value + (shares_value * close_value)

    return df

def plot_stock_data(data, ticker, initial_investment):
    # Handle the case where a column might be a DataFrame instead of a Series
    def ensure_series(column):
        if isinstance(column, pd.DataFrame):
            return column.squeeze()
        return column
    
    # Apply to relevant columns
    open_data = ensure_series(data['Open'])
    high_data = ensure_series(data['High'])
    low_data = ensure_series(data['Low'])
    close_data = ensure_series(data['Close'])
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, 
                        subplot_titles=(f'{ticker} Stock Price', 'MACD'),
                        specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

    # Plot stock price as candlesticks
    fig.add_trace(go.Candlestick(x=data.index,
                                 open=open_data,
                                 high=high_data,
                                 low=low_data,
                                 close=close_data,
                                 name='Price'),
                  row=1, col=1, secondary_y=False)

    # Add initial investment line on secondary y-axis
    fig.add_trace(go.Scatter(x=data.index, y=[initial_investment]*len(data), 
                             name='Initial Investment', 
                             line=dict(color='green', dash='dash')), 
                  row=1, col=1, secondary_y=True)

    # Filter buy/sell signals
    buy_signals = data[data['Buy_Signal'] == 1]
    sell_signals = data[data['Sell_Signal'] == 1]

    # Add buy and sell signals
    if not buy_signals.empty:
        buy_y_values = ensure_series(buy_signals['Low'])
        fig.add_trace(go.Scatter(x=buy_signals.index, 
                                y=buy_y_values,
                                mode='markers', 
                                name='Buy Signal', 
                                marker=dict(color='green', symbol='triangle-up', size=10)),
                    row=1, col=1, secondary_y=False)
                    
    if not sell_signals.empty:
        sell_y_values = ensure_series(sell_signals['High'])
        fig.add_trace(go.Scatter(x=sell_signals.index, 
                                y=sell_y_values,
                                mode='markers', 
                                name='Sell Signal', 
                                marker=dict(color='red', symbol='triangle-down', size=10)),
                    row=1, col=1, secondary_y=False)

    # Plot MACD with colors (ensure they're Series)
    macd_data = ensure_series(data['MACD'])
    signal_data = ensure_series(data['MACD_Signal'])
    
    fig.add_trace(go.Scatter(x=data.index, y=macd_data, name='MACD', line=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=signal_data, name='Signal Line', line=dict(color='red')), row=2, col=1)

    # Update layout
    fig.update_layout(height=800, width=1000, title_text=f"{ticker} Stock Analysis")
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])  # Hide weekends
    fig.update_yaxes(title_text="Price ($)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Investment ($)", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="MACD", row=2, col=1)

    # Update the range of the price axis
    close_data = ensure_series(data['Close'])
    price_range = close_data.max() - close_data.min()
    fig.update_yaxes(range=[close_data.min() - price_range*0.1, close_data.max() + price_range*0.1], row=1, col=1, secondary_y=False)

    return fig

def main():
    st.title('MACD Trading Strategy Visualizer')

    # Sidebar
    st.sidebar.header('User Input')
    tickers = st.sidebar.text_input('Enter stock tickers (comma-separated)', 'AAPL,GOOGL,MSFT').split(',')
    start_date = st.sidebar.date_input('Start Date', pd.to_datetime('2020-01-01'))
    end_date = st.sidebar.date_input('End Date', pd.to_datetime('2023-01-01'))
    
    initial_investment = st.sidebar.number_input('Initial Investment ($)', min_value=1000, max_value=1000000, value=10000, step=1000)
    
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

            # Ensure close_data is a Series
            close_data = data['Close'].squeeze() if isinstance(data['Close'], pd.DataFrame) else data['Close']
            portfolio_data = data['Portfolio'].squeeze() if isinstance(data['Portfolio'], pd.DataFrame) else data['Portfolio']
            
            # Handle potential Series values
            first_close = close_data.iloc[0]
            last_close = close_data.iloc[-1]
            if isinstance(first_close, pd.Series):
                first_close = float(first_close.iloc[0])
            if isinstance(last_close, pd.Series):
                last_close = float(last_close.iloc[0])
                
            final_portfolio_value = portfolio_data.iloc[-1]
            if isinstance(final_portfolio_value, pd.Series):
                final_portfolio_value = float(final_portfolio_value.iloc[0])
                
            # Display strategy performance
            buy_hold_return = (last_close - first_close) / first_close * 100
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
            position_data = data['Position'].squeeze() if isinstance(data['Position'], pd.DataFrame) else data['Position']
            current_position = "Holding" if position_data.iloc[-1] == 1 else "Not Holding"
            st.info(f"Current Position: {current_position}")
    
    
    st.markdown("""
    <style>
    .icon-button {
        display: inline-block;
        width: 100%;
        padding-bottom: 100%;
        position: relative;
        overflow: hidden;
    }

    .icon-button svg,
    .icon-button img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    </style>
    """, unsafe_allow_html=True)

    # Add "Made By" section to sidebar with icon buttons
    st.sidebar.header('Contact Me!')
    col1, col2, col3 = st.sidebar.columns(3)

    # GitHub icon
    github_icon = """
    <a href="https://github.com/varunbudati" target="_blank" class="icon-button">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
        </svg>
    </a>
    """
    with col1:
        st.markdown(github_icon, unsafe_allow_html=True)

    # Portfolio icon
    portfolio_icon = """
    <a href="https://varunbudati.github.io/" target="_blank" class="icon-button">
        <img src="https://varunbudati.github.io/assets/images/varun-budati.jpeg" alt="Portfolio Icon">
    </a>
    """
    with col2:
        st.markdown(portfolio_icon, unsafe_allow_html=True)

    # LinkedIn icon
    linkedin_icon = """
    <a href="https://www.linkedin.com/in/varun-budati" target="_blank" class="icon-button">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
        </svg>
    </a>
    """
    with col3:
        st.markdown(linkedin_icon, unsafe_allow_html=True)


if __name__ == '__main__':
    main()