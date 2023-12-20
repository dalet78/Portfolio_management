import pandas as pd
from libs.fibonacci import FibonacciRetracementCalculator
from libs.trend_analyzer import TrendAnalyzer
from libs.detectors.pivot_handler import PivotDetector
from libs.filtered_stock import return_filtred_list


def analyze_and_apply_fibonacci(df):
    """
    Apply Fibonacci retracement calculation for each trend segment identified in the DataFrame,
    using the length of the trend plus a 10-period buffer.

    :param df: DataFrame containing price data, a 'pivot' column, and a 'Trend' column.
    :return: DataFrame with Fibonacci retracement levels for each trend segment.
    """
    trend_analyzer = TrendAnalyzer(df)
    df_with_trend = trend_analyzer.add_trend_to_df()

    # Initialize Fibonacci level columns
    for level in ['23.6%', '38.2%', '50.0%', '61.8%', '100%']:
        df_with_trend[f'Fib_{level}'] = None

    # Track the start of the current trend
    start_of_trend = None
    current_trend = None

    for i in range(1, len(df_with_trend)):
        trend = df_with_trend['Trend'].iloc[i]

        # Detect a change in trend
        if trend != current_trend:
            current_trend = trend
            start_of_trend = i

        # If a trend is ongoing, calculate Fibonacci levels
        if start_of_trend is not None and trend != 0:
            trend_length = i - start_of_trend #+ 10   Including 10-period buffer
            trend_segment = df_with_trend.iloc[max(0, i - trend_length):i]

            if trend == 2:  # Ascending trend
                min_price = trend_segment['Low'].min()
                max_price = trend_segment['High'].max()
            elif trend == 1:  # Descending trend
                min_price = trend_segment['High'].max()
                max_price = trend_segment['Low'].min()
            else:
                continue  # Skip if no clear trend

            # Calculate Fibonacci levels for the segment
            fib_calculator = FibonacciRetracementCalculator(trend_segment)
            trend_segment = fib_calculator.add_fibonacci_levels(max_price, min_price)

            # Update the original DataFrame with the new Fibonacci levels
            for level in ['23.6%', '38.2%', '50.0%', '61.8%', '100%']:
                df_with_trend[f'Fib_{level}'].iloc[max(0, i - trend_length):i] = trend_segment[f'Fib_{level}']

    return df_with_trend


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
source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"

tickers_list = return_filtred_list(index='Russel')
for item in tickers_list:
    try:
        df = pd.read_csv(f"{source_directory}/Data/Russel/Daily/{item}_historical_data.csv",
                           parse_dates=['Date'])

        df_pivot= PivotDetector(df)
        df_new= df_pivot.add_pivot_column()

        df_with_signals = add_trading_signals(df_new)


# Example usage
# Assuming 'df' is your DataFrame with a 'pivot' column and price data
        df_with_fib = analyze_and_apply_fibonacci(df)
        print(df_with_fib)
    except FileNotFoundError:
        # Gestisci l'errore se il file non viene trovato
        print(f"File non trovato per {item}")
    except Exception as e:
        # Gestisci altri errori generici
        print(f"Errore durante l'elaborazione di {item}: {e}")
