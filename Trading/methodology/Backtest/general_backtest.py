import pandas as pd
import os, json
from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import matplotlib.pyplot as plt
from Trading.methodology.Indicators.triple_sma import EnhancedMovingAverageCrossoverStrategy
import numpy as np


class Backtester:
    def __init__(self, strategy, data):
        """
        Initialize the backtester with a trading strategy and historical data.

        Parameters:
        strategy (object): An instance of a trading strategy class.
        data (pd.DataFrame): DataFrame containing 'Close' prices for backtesting.
        """
        self.strategy = strategy
        self.data = data

    def execute_backtest(self):
        """
        Execute the backtest using the provided strategy and data.

        Returns:
        results (pd.DataFrame): DataFrame containing the backtest results.
        """
         # Apply the trading strategy
        signals = self.strategy.apply_strategy(self.data)

        # Initialize portfolio DataFrame to store the value of the portfolio
        portfolio = pd.DataFrame(index=signals.index)
        portfolio['holdings'] = 0.0
        portfolio['cash'] = 0.0

        # Adjust holdings and cash based on the signal
        for i in range(1, len(signals)):
            if signals['signal'][i] == 1.0:  # Long
                portfolio['holdings'][i] = portfolio['holdings'][i-1] + signals['adjusted_close'][i]
                portfolio['cash'][i] = portfolio['cash'][i-1] - signals['adjusted_close'][i]
            elif signals['signal'][i] == -1.0:  # Short
                portfolio['holdings'][i] = portfolio['holdings'][i-1] - signals['adjusted_close'][i]
                portfolio['cash'][i] = portfolio['cash'][i-1] + signals['adjusted_close'][i]
            else:  # Neutrale
                portfolio['holdings'][i] = portfolio['holdings'][i-1]
                portfolio['cash'][i] = portfolio['cash'][i-1]

        portfolio['total'] = portfolio['holdings'] + portfolio['cash']
        portfolio['returns'] = portfolio['total'].pct_change()
        portfolio['equity_curve'] = (1.0 + portfolio['returns']).cumprod()

        self.results = portfolio
        return portfolio

    def calculate_performance_metrics(self):
        """
        Calculate key performance metrics of the backtesting results.

        Returns:
        metrics (dict): Dictionary containing performance metrics.
        """
        if self.results.empty:
            return {'Total Return': None, 'Max Drawdown': None}

        total_return = self.results['total'].iloc[-1]  # Use iloc for safer access
        max_drawdown = self.results['total'].cummax() - self.results['total']
        max_drawdown_percent = max_drawdown.max()

        metrics = {
            'Total Return': total_return,
            'Max Drawdown': max_drawdown_percent
        }

        return metrics

def bt():
    # Using the same data and strategy as before
    with open("../../json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
    tickers_list = list(tickers.keys())
    enhanced_strategy = EnhancedMovingAverageCrossoverStrategy(short_window=10, long_window=50, extra_window=30, stop_loss_percent=0.05, take_profit_percent=0.10, transaction_cost=0.01, slippage=0.005)

    for item in tickers_list:
        data = pd.read_csv(f"Trading/Data/Daily/{item}_historical_data.csv")
        backtester = Backtester(enhanced_strategy, data)
        backtest_results = backtester.execute_backtest()
        performance_metrics = backtester.calculate_performance_metrics()
        print(backtest_results.tail(), performance_metrics)  # Display the last few rows and performance metrics

if __name__ == "__main__":
    bt()
    # comment