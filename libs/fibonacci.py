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

    def calculate_fibonacci_for_all_trends(self):
        """
        Identify all sequences of pivot highs and lows in the DataFrame and calculate Fibonacci retracement levels.
        :return: DataFrame with Fibonacci level columns added for each identified trend.
        """
        # Assuming the DataFrame has 'isPivot' column with 2 for pivot highs and 1 for pivot lows
        if 'isPivot' in self.df.columns:
            pivot_highs = self.df[self.df['isPivot'] == 2]
            pivot_lows = self.df[self.df['isPivot'] == 1]

            trend_counter = 0
            for high_index, high_row in pivot_highs.iterrows():
                for low_index, low_row in pivot_lows.iterrows():
                    if low_index > high_index:  # Identify a trend
                        trend_counter += 1
                        self.add_fibonacci_levels(high_row['High'], low_row['Low'], f'trend_{trend_counter}')
                        break  # Move to the next pivot high after processing a trend
        else:
            print("DataFrame does not contain pivot point information.")
        
        return self.df
