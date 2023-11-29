import pandas as pd
import json
import numpy as np

class EnhancedMovingAverageCrossoverStrategy:
    def __init__(self, params):
        """
        Initialize the enhanced moving average crossover strategy with an additional moving average for optimization.

        Parameters:
        short_window (int): Window size for the short-term moving average.
        long_window (int): Window size for the long-term moving average.
        extra_window (int): Window size for the additional moving average.
        stop_loss_percent (float): Percentage for stop loss.
        take_profit_percent (float): Percentage for take profit.
        transaction_cost (float): Fixed cost or percentage for each transaction.
        slippage (float): Slippage percentage to be applied to each trade.
        """
        self.short_window = params['short_window']
        self.long_window = params['long_window']
        self.extra_window = params['extra_window']
        self.stop_loss_percent = params['stop_loss_percent']
        self.take_profit_percent = params['take_profit_percent']
        self.transaction_cost = params.get('transaction_cost', 0.0)  # Default value if not present
        self.slippage = params.get('slippage', 0.0)  # Default value if not present

    def apply_strategy(self, data):
        """
        Apply the enhanced moving average crossover strategy to the provided data.

        Parameters:
        data (pd.DataFrame): DataFrame containing 'Close' prices.

        Returns:
        signals (pd.DataFrame): DataFrame with signals, stop loss, take profit, and adjusted prices considering slippage.
        """
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0

        # Calculate moving averages
        signals['short_mavg'] = data['Close'].rolling(window=self.short_window, min_periods=1).mean()
        signals['long_mavg'] = data['Close'].rolling(window=self.long_window, min_periods=1).mean()
        signals['extra_mavg'] = data['Close'].rolling(window=self.extra_window, min_periods=1).mean()

        # Create signals with an additional filter
        signals['signal'][self.short_window:] = np.where((signals['short_mavg'][self.short_window:] > signals['long_mavg'][self.short_window:]) & 
                                                       (signals['short_mavg'][self.short_window:] > signals['extra_mavg'][self.short_window:]), 
                                                       1.0, # Long
                                              np.where((signals['short_mavg'][self.short_window:] < signals['long_mavg'][self.short_window:]) & 
                                                       (signals['short_mavg'][self.short_window:] < signals['extra_mavg'][self.short_window:]), 
                                                       -1.0, # Short
                                                        0.0 # Neutrale
                                                        )
                                                    )
        signals['positions'] = signals['signal'].diff()

        # Calculate stop loss and take profit levels
        signals['stop_loss'] = data['Close'] * (1 - self.stop_loss_percent)
        signals['take_profit'] = data['Close'] * (1 + self.take_profit_percent)

        # Adjust for transaction cost and slippage
        signals['adjusted_close'] = data['Close'] * (1 + self.slippage) - self.transaction_cost

        return signals

#Example usage with the same mock data as before
with open("Trading/methodology/strategy_parameter.json", 'r') as file:
            param_data = json.load(file)
if param_data['Strategy']['name'] == "triple_sma":
    parameters_dict = param_data['Strategy']['parameters']

with open("json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
        tickers_list = list(tickers.keys())
    
enhanced_strategy = EnhancedMovingAverageCrossoverStrategy(parameters_dict)

for item in tickers_list:
    data = pd.read_csv(f"Trading/Data/Daily/{item}_historical_data.csv")
    enhanced_signals = enhanced_strategy.apply_strategy(data)
    print(enhanced_signals.tail())  # Display the last few rows to see the signals and adjusted prices
