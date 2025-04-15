from flask import Flask, render_template, request, jsonify
import pandas as pd
import yfinance as yf
import numpy as np
import ta
import json
from datetime import datetime

app = Flask(__name__)

def get_stock_data(ticker, start_date, end_date):
    # Ensure that start_date is before end_date
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Swap if necessary
    if start > end:
        start_date, end_date = end_date, start_date
        print(f"Warning: Start date was after end date. Swapped to: start={start_date}, end={end_date}")
    
    try:
        stock_data = yf.download(ticker, start=start_date, end=end_date)
        # Check if we got any data
        if stock_data.empty:
            print(f"No data found for {ticker} between {start_date} and {end_date}")
            return pd.DataFrame()  # Return empty DataFrame
        
        # Updated to use ffill() instead of deprecated fillna(method='ffill')
        stock_data.ffill(inplace=True)
        return stock_data
    except Exception as e:
        print(f"Error downloading data for {ticker}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

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
    
    # For debugging
    print(f"Type of Close data: {type(data['Close'])}")
    print(f"Shape of Close data: {data['Close'].shape if hasattr(data['Close'], 'shape') else 'N/A'}")
    print(f"Type of close_series: {type(close_series)}")
    print(f"Shape of close_series: {close_series.shape if hasattr(close_series, 'shape') else 'N/A'}")
    
    return data

def generate_signals(data):
    data['Buy_Signal'] = ((data['MACD'] > data['MACD_Signal']) & 
                          (data['MACD'].shift(1) <= data['MACD_Signal'].shift(1))).astype(int)
    data['Sell_Signal'] = ((data['MACD'] < data['MACD_Signal']) & 
                           (data['MACD'].shift(1) >= data['MACD_Signal'].shift(1))).astype(int)
    return data

def implement_trading_strategy(data, initial_capital=10000.0):
    # Create a copy of the input DataFrame
    df = data.copy()
    
    # Create new columns with default values
    df['Position'] = 0  # 1 for long, -1 for short, 0 for neutral
    df['Trade'] = 0  # 1 for buy, -1 for sell
    df['Portfolio'] = float(initial_capital)  # Explicitly set as float

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data_api():
    print("Received request for stock data")
    try:
        # Check if we're receiving single ticker or multiple tickers
        if 'tickers' in request.form:
            tickers = json.loads(request.form['tickers'])
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            
            print(f"Tickers: {tickers}, Start Date: {start_date}, End Date: {end_date}")
            
            response_data = {}
            
            for ticker in tickers:
                data = get_stock_data(ticker, start_date, end_date)
                
                # Skip if no data was found for this ticker
                if data.empty:
                    response_data[ticker] = {
                        'error': f"No data found for {ticker} between {start_date} and {end_date}"
                    }
                    continue
                
                data = calculate_indicators(data)
                data = generate_signals(data)
                data = implement_trading_strategy(data)
                
                # Helper function to convert NaN to None
                def nan_to_none(value):
                    return None if isinstance(value, (float, np.float64)) and np.isnan(value) else value

                # Helper function to convert DataFrame column to list
                def df_column_to_list(column):
                    if isinstance(column, pd.DataFrame):
                        return [nan_to_none(x) for x in column.squeeze().tolist()]
                    else:
                        return [nan_to_none(x) for x in column.tolist()]

                response_data[ticker] = {
                    'dates': data.index.strftime('%Y-%m-%d').tolist(),
                    'close': df_column_to_list(data['Close']),
                    'macd': df_column_to_list(data['MACD']),
                    'signal': df_column_to_list(data['MACD_Signal']),
                    'buy_signals': data[data['Buy_Signal'] == 1].index.strftime('%Y-%m-%d').tolist(),
                    'sell_signals': data[data['Sell_Signal'] == 1].index.strftime('%Y-%m-%d').tolist(),
                    'portfolio': df_column_to_list(data['Portfolio'])
                }
            
            print("Response data prepared")
            return jsonify(response_data)
        else:
            # Single ticker handling
            ticker = request.form['ticker']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            
            print(f"Ticker: {ticker}, Start Date: {start_date}, End Date: {end_date}")
            
            data = get_stock_data(ticker, start_date, end_date)
            
            # Check if we got any data
            if data.empty:
                return jsonify({
                    'error': f"No data found for {ticker} between {start_date} and {end_date}"
                }), 404
                
            print("Stock data fetched successfully")
            print(data.head())

            data = calculate_indicators(data)
            print("Indicators calculated")
            print(data.head())

            data = generate_signals(data)
            print("Signals generated")
            print(data.head())

            data = implement_trading_strategy(data)
            print("Trading strategy implemented")
            print(data.head())
            
            # Helper function to convert NaN to None
            def nan_to_none(value):
                return None if isinstance(value, (float, np.float64)) and np.isnan(value) else value

            # Helper function to convert DataFrame column to list
            def df_column_to_list(column):
                if isinstance(column, pd.DataFrame):
                    return [nan_to_none(x) for x in column.squeeze().tolist()]
                else:
                    return [nan_to_none(x) for x in column.tolist()]

            response_data = {
                'dates': data.index.strftime('%Y-%m-%d').tolist(),
                'close': df_column_to_list(data['Close']),
                'macd': df_column_to_list(data['MACD']),
                'signal': df_column_to_list(data['MACD_Signal']),
                'buy_signals': data[data['Buy_Signal'] == 1].index.strftime('%Y-%m-%d').tolist(),
                'sell_signals': data[data['Sell_Signal'] == 1].index.strftime('%Y-%m-%d').tolist(),
                'portfolio': df_column_to_list(data['Portfolio'])
            }
            
            print("Response data prepared")
            return jsonify(response_data)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)