# MACD Trading Strategy Visualizer

This project is a web-based stock trading dashboard that implements a momentum trading strategy using technical indicators. It allows users to analyze stock data, visualize trading signals, and simulate portfolio performance.

![image](https://github.com/user-attachments/assets/8240a953-6816-4cc2-8e57-7d78b72ec425)

## Features

- Fetch historical stock data for multiple tickers
- Calculate technical indicators (MACD, RSI)
- Generate buy/sell signals based on MACD crossovers
- Implement a simple trading strategy
- Visualize stock prices, indicators, and trading signals
- Simulate portfolio performance

## Technologies Used

- Backend: Python, Flask
- Frontend: HTML, JavaScript, CSS
- Data Analysis: pandas, numpy, yfinance, ta (Technical Analysis library)
- Visualization: matplotlib 

## Setup and Installation

1. Clone the repository:
2. 		git clone https://github.com/varunbudati/MACD-Trading-Strategy-Visualizer.git
3. 		cd MACD-Trading-Strategy-Visualizer
4. Install required Python packages:
pip install flask pandas numpy yfinance ta matplotlib
5. Run the Flask application:
python app.py
6. Open a web browser and navigate to `http://localhost:5000` to access the dashboard.

## Usage

1. Select one or more stock tickers from the preset list or add custom tickers.
2. Choose a date range for analysis.
3. Click "Get Data" to fetch and analyze the stock data.
4. View the generated charts showing stock prices, MACD indicators, and buy/sell signals.
5. Analyze the simulated portfolio performance based on the implemented trading strategy.

## Project Structure

- `app.py`: Flask application serving as the backend
- `Trading.py`: Contains core functions for data processing and strategy implementation
- `index.html`: Frontend HTML template for the dashboard

## Contributing

Contributions to improve the project are welcome. Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes and commit (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Create a new Pull Request


## Disclaimer

This project is for educational purposes only. The implemented trading strategy is a basic example and should not be used for actual trading without thorough testing and risk management considerations.

## Images From Execution

![image](https://github.com/user-attachments/assets/e78ba219-f89e-4f36-a841-904da8397e08)



![image](https://github.com/user-attachments/assets/1c02dae0-3a75-43ac-8c46-ed4cde7d182a)

![image](https://github.com/user-attachments/assets/2c8e93c7-2364-4d83-83d3-a51484141cfa)
