import json
import pandas as pd

def check_cross_levels(dataframe, levels, use_ohlc=False):
    """
    Determine if there is a cross at the current point through any of the given levels and classify the type of cross:
    Type 2 for an upward cross, and Type 1 for a downward cross.

    :param dataframe: Pandas DataFrame with trading data.
    :param levels: List containing both support and resistance levels.
    :param use_ohlc: Boolean indicating whether to use OHLC data (True) or just Open and Close (False).
    :return: DataFrame with additional columns 'cross_type' and 'crossed_level'.
    """
    # Initialize new columns
    dataframe['cross_type'] = 0
    dataframe['crossed_level'] = None

    for i in range(1, len(dataframe)):
        current_open = dataframe.at[i, 'Open']
        current_close = dataframe.at[i, 'Close']

        # Use OHLC data if specified
        if use_ohlc:
            current_high = dataframe.at[i, 'High']
            current_low = dataframe.at[i, 'Low']

        for level in levels:
            if use_ohlc:
                crossed_upward = current_low < level <= current_high
                crossed_downward = current_high > level >= current_low
            else:
                crossed_upward = current_open < level <= current_close
                crossed_downward = current_open > level >= current_close

            if crossed_upward:
                dataframe.at[i, 'cross_type'] = 2
                dataframe.at[i, 'crossed_level'] = level
                break
            elif crossed_downward:
                dataframe.at[i, 'cross_type'] = 1
                dataframe.at[i, 'crossed_level'] = level
                break

    return dataframe


def check_cross_levels_with_lookback(dataframe, levels, lookback_periods=5, use_ohlc=False):
    """
    Determine if there has been a cross through any of the given levels in the last 'lookback_periods'.

    :param dataframe: Pandas DataFrame with trading data.
    :param levels: List containing both support and resistance levels.
    :param lookback_periods: Number of periods to look back, default is 5.
    :param use_ohlc: Boolean indicating whether to use OHLC data (True) or just Open and Close (False).
    :return: DataFrame with additional columns 'cross_type', 'crossed_level', and 'cross_period_ago'.
    """
    # Ensure the lookback period is not greater than the dataframe length
    lookback_periods = min(lookback_periods, len(dataframe))

    # Initialize new columns
    dataframe['cross_type'] = 0
    dataframe['crossed_level'] = None
    dataframe['cross_period_ago'] = None

    for i in range(len(dataframe)):
        # Look back only up to 'lookback_periods' or start of the dataframe
        start_index = max(0, i - lookback_periods)
        end_index = i

        # Extract the relevant slice of the dataframe
        recent_data = dataframe.iloc[start_index:end_index]
        
        for level in levels:
            # Initialize variables to check for cross
            crossed_below = crossed_above = cross_occurred = False

            if use_ohlc:
                high = recent_data['High']
                low = recent_data['Low']
                current_high = dataframe.at[i, 'High']
                current_low = dataframe.at[i, 'Low']

                crossed_below = (low.shift(-1) < level) & (current_high > level)
                crossed_above = (high.shift(-1) > level) & (current_low < level)
            else:
                close = recent_data['Close']
                current_close = dataframe.at[i, 'Close']

                crossed_below = close.shift(-1) < level
                crossed_above = close.shift(-1) > level

            cross_occurred = crossed_below | crossed_above

            if cross_occurred.any():
                # Determine the cross type and the period ago it happened
                cross_type = 2 if current_close > level else 1
                cross_period_ago = cross_occurred[::-1].idxmax() - i

                # Update the DataFrame
                dataframe.at[i, 'cross_type'] = cross_type
                dataframe.at[i, 'crossed_level'] = level
                dataframe.at[i, 'cross_period_ago'] = abs(cross_period_ago)
                break  # Stop checking further levels once a cross is found

    return dataframe

def check_pre_cross_break(dataframe, level, lookback_periods=5, check_periods=20, use_ohlc=False):
    """
    Check if, before a cross event in the last 'lookback_periods', the dataframe [20-n:-n]
    did not break the previous support/resistance level.

    :param dataframe: Pandas DataFrame with trading data.
    :param level: The support or resistance level to check.
    :param lookback_periods: Number of periods to look back for a cross event, default is 5.
    :param check_periods: Number of periods before the lookback period to check for breaks.
    :param use_ohlc: Boolean indicating whether to use OHLC data (True) or just Open and Close (False).
    :return: DataFrame with an additional 'pre_cross_break' column indicating if a break occurred.
    """
    # Ensure parameters are within the dataframe's length
    lookback_periods = min(lookback_periods, len(dataframe))
    check_periods = min(check_periods, len(dataframe) - lookback_periods)

    # Initialize the 'pre_cross_break' column
    dataframe['pre_cross_break'] = 0

    for i in range(len(dataframe)):
        # Only check if the current period is within the last 'lookback_periods'
        if i >= len(dataframe) - lookback_periods:
            start_index = max(0, i - check_periods - lookback_periods)
            end_index = max(0, i - lookback_periods)

            # Extract the relevant slice of the dataframe
            pre_cross_data = dataframe.iloc[start_index:end_index]

            # Initialize variable to check for break
            break_occurred = False

            if use_ohlc:
                high = pre_cross_data['High']
                low = pre_cross_data['Low']

                break_occurred = ((high > level) & (low < level)).any()
            else:
                open_price = pre_cross_data['Open']
                close_price = pre_cross_data['Close']

                break_occurred = ((open_price > level) & (close_price < level)) | \
                                 ((open_price < level) & (close_price > level))

            # Update the DataFrame
            dataframe.at[i, 'pre_cross_break'] = break_occurred

    return dataframe

def analyze_cross_trend_condition(dataframe):
    """
    Analyze the DataFrame and add a new column 'trend_condition_met' indicating whether the trend condition
    is met for each cross. For a cross of type 2, the condition is met if the pivot_high_trend for the last
    pivot point (isPivot) - 2 is True. For a cross of type 1, the condition is met if the pivot_low_trend 
    for the last pivot point (isPivot) - 2 is True.

    :param dataframe: Pandas DataFrame with market data including 'isPivot', 'cross_type', 
                      'pivot_high_trend', and 'pivot_low_trend' columns.
    :return: Modified DataFrame with an added 'trend_condition_met' column.
    """
    dataframe['trend_condition_met'] = False

    for i in range(len(dataframe)):
        if dataframe.at[i, 'cross_type'] == 2:
            # Identificare il penultimo punto pivot prima del cross
            prev_pivots = dataframe[dataframe['isPivot'] > 0].iloc[:i]
            if len(prev_pivots) >= 2:
                trend_condition = prev_pivots.iloc[-2]['pivot_high_trend']
                dataframe.at[i, 'trend_condition_met'] = trend_condition

        elif dataframe.at[i, 'cross_type'] == 1:
            # Identificare il penultimo punto pivot prima del cross
            prev_pivots = dataframe[dataframe['isPivot'] > 0].iloc[:i]
            if len(prev_pivots) >= 2:
                trend_condition = prev_pivots.iloc[-2]['pivot_low_trend']
                dataframe.at[i, 'trend_condition_met'] = trend_condition

    return dataframe



