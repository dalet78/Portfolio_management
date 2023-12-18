import pandas as pd

class FibonacciRetracementCalculator:
    def __init__(self, df):
        """
        Initialize the FibonacciRetracementCalculator class with a DataFrame.
        :param df: DataFrame containing the price data.
        """
        self.df = df

    def add_fibonacci_levels(self, pivot_high, pivot_low):
        """
        Calculate Fibonacci retracement levels and add them as columns to the DataFrame.
        :param pivot_high: The highest price in the current trend.
        :param pivot_low: The lowest price in the current trend.
        :return: DataFrame with Fibonacci level columns added.
        """
        difference = pivot_high - pivot_low
        fib_levels = {
            '23.6%': pivot_high - difference * 0.236,
            '38.2%': pivot_high - difference * 0.382,
            '50.0%': pivot_high - difference * 0.5,
            '61.8%': pivot_high - difference * 0.618,
            '100%': pivot_low
        }

        for key, value in fib_levels.items():
            self.df[f'Fib_{key}'] = value

        return self.df
