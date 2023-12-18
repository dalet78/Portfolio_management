def analyze_and_apply_fibonacci(df):
    """
    Analyze the trend of the given DataFrame and apply Fibonacci retracement calculation 
    based on the trend. For an ascending trend, it finds the min and max values of the last 
    20 periods. For a descending trend, it reverses this logic.
    
    :param df: DataFrame containing price data and a 'pivot' column.
    :return: DataFrame with Fibonacci retracement levels, if applicable.
    """
    # Analyze the trend
    trend_analyzer = TrendAnalyzer(df)
    df_with_trend = trend_analyzer.add_trend_column()

    # Check the current trend
    current_trend = df_with_trend['Trend'].iloc[-1]

    if len(df) >= 20:
        recent_df = df.iloc[-20:]

        if current_trend == 2:  # Ascending trend
            min_price = recent_df['Low'].min()
            max_price = recent_df['High'].max()
        elif current_trend == 1:  # Descending trend
            min_price = recent_df['High'].max()
            max_price = recent_df['Low'].min()
        else:
            return df  # Return original DataFrame if no clear trend

        # Apply Fibonacci retracement
        fib_calculator = FibonacciRetracementCalculator(df)
        df_with_fib_levels = fib_calculator.add_fibonacci_levels(max_price, min_price)

        return df_with_fib_levels

    # Return the original DataFrame if not enough data
    return df

def add_trading_signals(df):
    """
    Add trading signals to the DataFrame. Signal '2' for buy, '1' for sell, and '0' for no signal.
    Buy signals are generated in an ascending trend when the price is near SMA21 and a Fibonacci level.
    Sell signals are generated in a descending trend under the same conditions but in reverse.
    """
    # Calculate the SMA21
    df['SMA21'] = df['Close'].rolling(window=21).mean()

    # Apply Trend Analyzer and Fibonacci Retracement
    df_with_trend = analyze_and_apply_fibonacci(df)

    # Initialize the 'Signal' column
    df_with_trend['Signal'] = 0

    # Threshold for being 'close' to a Fibonacci level or SMA21
    threshold = 0.03  # 3% for example, adjust based on your criteria

    # Last row of the DataFrame
    last_row = df_with_trend.iloc[-1]

    for fib_level in ['Fib_23.6%', 'Fib_38.2%', 'Fib_50.0%', 'Fib_61.8%']:
        if last_row['Trend'] == 2 and abs(last_row['Close'] - last_row['SMA21']) / last_row['Close'] <= threshold:
            if abs(last_row['Close'] - last_row[fib_level]) / last_row['Close'] <= threshold:
                df_with_trend.at[len(df_with_trend) - 1, 'Signal'] = 2  # Buy signal
                break
        elif last_row['Trend'] == 1 and abs(last_row['Close'] - last_row['SMA21']) / last_row['Close'] <= threshold:
            if abs(last_row['Close'] - last_row[fib_level]) / last_row['Close'] <= threshold:
                df_with_trend.at[len(df_with_trend) - 1, 'Signal'] = 1  # Sell signal
                break

    return df_with_trend

# Example usage
df_with_signals = add_trading_signals(df)
print(df_with_signals)

# Example usage
# Assuming 'df' is your DataFrame with a 'pivot' column and price data
df_with_fib = analyze_and_apply_fibonacci(df)
print(df_with_fib)
