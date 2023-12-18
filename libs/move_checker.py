class TrendAnalyzer:
    def __init__(self, df):
        """
        Initialize the TrendAnalyzer class with a DataFrame.
        :param df: DataFrame containing price data and a 'pivot' column.
        """
        self.df = df


    def determine_trend(self):
        """
        Determine the trend direction based on pivot highs and lows.
        A trend is considered ascending if at least the last three pivot highs are increasing and at least two pivot lows are increasing.
        It's considered descending if the opposite is true.
        :return: 2 for an ascending trend, 1 for a descending trend, 0 for lateral.
        """
        pivot_highs = self.df[self.df['pivot'] == 2]
        pivot_lows = self.df[self.df['pivot'] == 1]

        # Check if there are enough pivot points to determine a trend
        if len(pivot_highs) < 3 or len(pivot_lows) < 2:
            return 0  # Not enough data to determine the trend

        # Check if the last three pivot highs are increasing
        if all(pivot_highs.iloc[-i]['Close'] < pivot_highs.iloc[-(i + 1)]['Close'] for i in range(1, 3)):
            # Check if the last two pivot lows are increasing
            if all(pivot_lows.iloc[-i]['Close'] < pivot_lows.iloc[-(i + 1)]['Close'] for i in range(1, 2)):
                return 2  # Ascending trend
        # Check for descending trend (opposite conditions)
        elif all(pivot_highs.iloc[-i]['Close'] > pivot_highs.iloc[-(i + 1)]['Close'] for i in range(1, 3)):
            if all(pivot_lows.iloc[-i]['Close'] > pivot_lows.iloc[-(i + 1)]['Close'] for i in range(1, 2)):
                return 1  # Descending trend

        return 0  # Lateral trend
