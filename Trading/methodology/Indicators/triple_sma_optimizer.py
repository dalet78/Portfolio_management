from itertools import product
from portfolio_management.Trading.methodology.Indicators.triple_sma import EnhancedMovingAverageCrossoverStrategy
from portfolio_management.Trading.methodology.Indicators.triple_sma_backtest import Backtester
import numpy as np

class SMAOptimizer:
    def __init__(self, data, short_window_range, long_window_range, extra_window_range):
        """
        Initialize the SMA optimizer.

        Parameters:
        data (pd.DataFrame): DataFrame containing 'Close' prices for optimization.
        short_window_range (range): Range of values to test for the short-term moving average.
        long_window_range (range): Range of values to test for the long-term moving average.
        extra_window_range (range): Range of values to test for the additional moving average.
        """
        self.data = data
        self.short_window_range = short_window_range
        self.long_window_range = long_window_range
        self.extra_window_range = extra_window_range

    def optimize(self, metric='Total Return'):
        """
        Execute the optimization process.

        Parameters:
        metric (str): The performance metric to maximize. Default is 'Total Return'.

        Returns:
        best_params (dict): Dictionary containing the best parameters found.
        best_metric_value (float): Value of the performance metric for the best parameters.
        """
        best_metric_value = float('-inf')
        best_params = None

        for short_window, long_window, extra_window in product(self.short_window_range, self.long_window_range, self.extra_window_range):
            # Skip if short_window is not shorter than long_window or extra_window
            if short_window >= long_window or short_window >= extra_window:
                continue

            # Initialize and backtest the strategy with current set of parameters
            strategy = EnhancedMovingAverageCrossoverStrategy(short_window, long_window, extra_window, stop_loss_percent=0.05, take_profit_percent=0.10)
            backtester = Backtester(strategy, self.data)
            backtester.execute_backtest()
            performance_metrics = backtester.calculate_performance_metrics()

            # Check if the current metric is better than the best one found so far
            if performance_metrics[metric] > best_metric_value:
                best_metric_value = performance_metrics[metric]
                best_params = {'short_window': short_window, 'long_window': long_window, 'extra_window': extra_window}

        return best_params, best_metric_value

# Example usage of SMAOptimizer
# Let's assume the same data as before and define ranges for each SMA window
# with open("portfolio_management/json_files/SP500-stock.json", 'r') as file:
#         tickers = json.load(file)
#         tickers_list = list(tickers.keys())
    
# enhanced_strategy = EnhancedMovingAverageCrossoverStrategy(short_window=10, long_window=50, extra_window=30, stop_loss_percent=0.05, take_profit_percent=0.10, transaction_cost=0.01, slippage=0.005)

# for item in tickers_list:
#     data = pd.read_csv(f"portfolio_management/Trading/Data/Daily/{item}_historical_data.csv")
#     optimizer = SMAOptimizer(data, short_window_range=range(5, 15), long_window_range=range(30, 60, 10), extra_window_range=range(20, 50, 10))
#     best_params, best_metric_value = optimizer.optimize(metric='Total Return')

#     print(best_params, best_metric_value)  # Display the best parameters and the corresponding performance metric value
