import pandas as pd
import talib

#pip install TA-Lib

class CandlestickPatternDetector:
    def __init__(self, df):
        """
        Initialize the CandlestickPatternDetector class with a DataFrame.
        The DataFrame should have 'Open', 'High', 'Low', and 'Close' columns.
        """
        self.df = df

    def identify_patterns(self):
        """
        Identifies various candlestick patterns and adds them as columns to the DataFrame.
        Each column represents one pattern with boolean values (True if the pattern is identified).
        """
        # List of candlestick patterns to identify
        pattern_names = talib.get_function_groups()['Pattern Recognition']

        # Iterate over the pattern names and apply the corresponding TA-Lib function
        for name in pattern_names:
            pattern_function = getattr(talib, name)
            self.df[name] = pattern_function(self.df['Open'], self.df['High'], self.df['Low'], self.df['Close'])

        return self.df

# Example usage
# Assuming you have a DataFrame 'df' with 'Open', 'High', 'Low', 'Close' columns
pattern_detector = CandlestickPatternDetector(df)
df_with_patterns = pattern_detector.identify_patterns()
print(df_with_patterns)
