from flask import Flask, render_template, request, jsonify
import pandas as pd
import yfinance as yf
import numpy as np
import ta
import json

app = Flask(__name__)

def get_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    stock_data.fillna(method='ffill', inplace=True)
    return stock_data

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
        tickers = json.loads(request.form['tickers'])
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        print(f"Tickers: {tickers}, Start Date: {start_date}, End Date: {end_date}")
        
        response_data = {}
        
        for ticker in tickers:
            data = get_stock_data(ticker, start_date, end_date)
            data = calculate_indicators(data)
            data = generate_signals(data)
            data = implement_trading_strategy(data)
            
            # Helper function to convert NaN to None
            def nan_to_none(value):
                return None if isinstance(value, (float, np.float64)) and np.isnan(value) else value

            response_data[ticker] = {
                'dates': data.index.strftime('%Y-%m-%d').tolist(),
                'close': [nan_to_none(x) for x in data['Close'].tolist()],
                'macd': [nan_to_none(x) for x in data['MACD'].tolist()],
                'signal': [nan_to_none(x) for x in data['MACD_Signal'].tolist()],
                'buy_signals': data[data['Buy_Signal'] == 1].index.strftime('%Y-%m-%d').tolist(),
                'sell_signals': data[data['Sell_Signal'] == 1].index.strftime('%Y-%m-%d').tolist(),
                'portfolio': [nan_to_none(x) for x in data['Portfolio'].tolist()]
            }
        
        print("Response data prepared")
        return jsonify(response_data)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500
    print("Received request for stock data")
    try:
        ticker = request.form['ticker']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        print(f"Ticker: {ticker}, Start Date: {start_date}, End Date: {end_date}")
        
        data = get_stock_data(ticker, start_date, end_date)
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

        response_data = {
            'dates': data.index.strftime('%Y-%m-%d').tolist(),
            'close': [nan_to_none(x) for x in data['Close'].tolist()],
            'macd': [nan_to_none(x) for x in data['MACD'].tolist()],
            'signal': [nan_to_none(x) for x in data['MACD_Signal'].tolist()],
            'buy_signals': data[data['Buy_Signal'] == 1].index.strftime('%Y-%m-%d').tolist(),
            'sell_signals': data[data['Sell_Signal'] == 1].index.strftime('%Y-%m-%d').tolist(),
            'portfolio': [nan_to_none(x) for x in data['Portfolio'].tolist()]
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