from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
import pandas as pd
from libs.detectors.pivot_handler import PivotDetector
from libs.detectors.support_resistence_handler import SupportResistanceFinder
from libs.filtered_stock import return_filtred_list
import time


def check_cross_levels(dataframe, levels, lookback_periods=5):
    """
    Determine if there has been a cross through any of the given levels in the last 'lookback_periods'.

    :param dataframe: Pandas DataFrame with trading data.
    :param levels: List containing both support and resistance levels without distinction.
    :param lookback_periods: Number of periods to look back, default is 5.
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
        current_price = dataframe.at[i, 'Close']

        for level in levels:
            # Check if there was a cross in the recent data
            crossed_below = recent_data['Close'].shift(-1) < level
            crossed_above = recent_data['Close'].shift(-1) > level
            cross_occurred = (crossed_below & (current_price > level)) | (crossed_above & (current_price < level))

            if cross_occurred.any():
                # Determine the cross type and the period ago it happened
                cross_type = 2 if current_price > level else 1
                cross_period_ago = cross_occurred[::-1].idxmax() - i

                # Update the DataFrame
                dataframe.at[i, 'cross_type'] = cross_type
                dataframe.at[i, 'crossed_level'] = level
                dataframe.at[i, 'cross_period_ago'] = abs(cross_period_ago)
                break  # Stop checking further levels once a cross is found

    return dataframe


def check_pre_cross_break(dataframe, level, lookback_periods=5, check_periods=20):
    """
    Check if, before a cross event in the last 'lookback_periods', the dataframe [20-n:-n]
    did not break the previous support/resistance level.

    :param dataframe: Pandas DataFrame with trading data containing 'Open' and 'Close' columns.
    :param levels: List containing both support and resistance levels without distinction.
    :param lookback_periods: Number of periods to look back for a cross event, default is 5.
    :param check_periods: Number of periods before the lookback period to check for breaks.
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

            # Check if there was a break of any level in pre_cross_data
            break_occurred = 0
            if (((pre_cross_data['Open'] > level) & (pre_cross_data['Close'] < level)) |
                    ((pre_cross_data['Open'] < level) & (pre_cross_data['Close'] > level))).any():
                break_occurred = 1
                break

            # Update the DataFrame
            dataframe.at[i, 'pre_cross_break'] = break_occurred

    return dataframe


def verify_breakout_volume(dataframe, lookback_volume=10):
    """
    Check if the volume on the day of a cross is greater than 1.5 times the average volume of the last 'lookback_volume' days.

    :param dataframe: Pandas DataFrame with trading data containing 'cross_type', 'crossed_level', 'cross_period_ago', and 'Volume'.
    :param lookback_volume: Number of days to calculate the average volume, default is 10.
    :return: DataFrame with an additional 'verify_breakout_volume' column.
    """
    # Ensure the lookback period is not greater than the dataframe length
    lookback_volume = min(lookback_volume, len(dataframe))

    # Initialize the 'verify_breakout_volume' column
    dataframe['verify_breakout_volume'] = 0

    for i in range(len(dataframe)):
        # Only proceed if a cross occurred
        if dataframe.at[i, 'cross_type'] != 0:
            # Calculate the average volume for the lookback period
            start_index = max(0, i - lookback_volume)
            average_volume = dataframe.iloc[start_index:i]['Volume'].mean()

            # Get the volume on the day of the cross
            cross_volume = dataframe.at[i, 'Volume']

            # Compare and update the 'verify_breakout_volume' column
            if 1.5 * average_volume <= cross_volume < 2.2 * average_volume:
                dataframe.at[i, 'verify_breakout_volume'] = 1
            elif cross_volume >= 2.2 * average_volume:
                dataframe.at[i, 'verify_breakout_volume'] = 2

    return dataframe


def check_inverse_cross(dataframe, lookback_period=4):
    """
    Check if, after a breakout, the 'crossed_level' has not been crossed inversely with High, Low, Open, Close (HLOC)
    values in the last 2 to 4 days.

    :param dataframe: Pandas DataFrame with trading data containing 'crossed_level', 'cross_type', and HLOC values.
    :param lookback_period: Number of days to check for an inverse cross, default is 4.
    :return: DataFrame with an additional 'inverse_cross' column.
    """
    # Ensure the lookback period is not greater than the dataframe length
    lookback_period = min(lookback_period, len(dataframe))

    # Initialize the 'inverse_cross' column
    dataframe['inverse_cross'] = False

    for i in range(len(dataframe)):
        # Only proceed if a cross occurred
        if dataframe.at[i, 'cross_type'] != 0:
            crossed_level = dataframe.at[i, 'crossed_level']
            cross_type = dataframe.at[i, 'cross_type']

            # Determine the lookback range
            start_index = max(0, i + 1)
            end_index = min(i + lookback_period + 1, len(dataframe))

            # Extract the relevant slice of the dataframe
            post_cross_data = dataframe.iloc[start_index:end_index]

            # Check for an inverse cross
            if cross_type == 1:  # Initially crossed upwards
                # Check if 'crossed_level' is crossed downwards in the lookback period
                inverse_cross_occurred = (
                        (post_cross_data['High'] >= crossed_level) &
                        (post_cross_data['Low'] <= crossed_level)
                ).any()
            elif cross_type == 2:  # Initially crossed downwards
                # Check if 'crossed_level' is crossed upwards in the lookback period
                inverse_cross_occurred = (
                        (post_cross_data['Low'] <= crossed_level) &
                        (post_cross_data['High'] >= crossed_level)
                ).any()

            # Update the DataFrame
            dataframe.at[i, 'inverse_cross'] = inverse_cross_occurred

    return dataframe


def check_pivot_trends_with_sl(dataframe):
    """
    Set 'pivot_high_trend' to True for all rows between two increasing pivot highs,
    and 'pivot_low_trend' to True for all rows between two decreasing pivot lows.
    Also, set the stop loss value based on the last pivot.

    :param dataframe: Pandas DataFrame with columns 'isPivot', 'Price', 'High', 'Low'.
                      'isPivot' - 2 indicates a pivot high and 1 indicates a pivot low.
    :return: Updated DataFrame with new columns 'pivot_high_trend', 'pivot_low_trend', 'stop_loss'.
    """

    # Initialize trend indicators and stop loss
    dataframe['pivot_high_trend'] = False
    dataframe['pivot_low_trend'] = False
    dataframe['stop_loss'] = None

    # Calculate pivot high and low trends
    last_pivot_high_idx = None
    last_pivot_low_idx = None
    last_pivot_high_value = None
    last_pivot_low_value = None

    for i, row in dataframe.iterrows():
        if row['isPivot'] == 2:  # Pivot High
            if last_pivot_high_value is not None and row['High'] > last_pivot_high_value:
                dataframe.loc[last_pivot_high_idx:i, 'pivot_high_trend'] = True
            last_pivot_high_idx = i
            last_pivot_high_value = row['High']

        elif row['isPivot'] == 1:  # Pivot Low
            if last_pivot_low_value is not None and row['Low'] < last_pivot_low_value:
                dataframe.loc[last_pivot_low_idx:i, 'pivot_low_trend'] = True
            last_pivot_low_idx = i
            last_pivot_low_value = row['Low']

        # Set stop loss based on the last pivot
        if row['isPivot'] == 2 and last_pivot_low_value is not None:
            dataframe.at[i, 'stop_loss'] = last_pivot_low_value
        elif row['isPivot'] == 1 and last_pivot_high_value is not None:
            dataframe.at[i, 'stop_loss'] = last_pivot_high_value

    return dataframe


def add_new_level_to_dataframe(dataframe, lookback_period=4):
    """
    Add the new support or resistance level to the DataFrame based on the latest cross type and inverse cross status,
    considering the maximum/minimum value of the last 'lookback_period - 1' periods.

    :param dataframe: Pandas DataFrame with trading data containing 'cross_type', 'inverse_cross', and HLOC values.
    :param lookback_period: Number of days to look back, default is 4.
    :return: DataFrame with an additional 'new_level' column.
    """
    # Adjust the lookback period
    adjusted_lookback = lookback_period - 1

    # Ensure the adjusted lookback period is within the dataframe's length and greater than zero
    adjusted_lookback = max(1, min(adjusted_lookback, len(dataframe)))

    # Initialize the 'new_level' column
    dataframe['new_level'] = None

    for i in range(len(dataframe)):
        # Determine the lookback range
        start_index = max(0, i - adjusted_lookback)
        end_index = min(i + 1, len(dataframe))
        lookback_data = dataframe.iloc[start_index:end_index]

        if lookback_data['inverse_cross'].iloc[-1] == 0:
            if lookback_data['cross_type'].iloc[-1] == 2:
                # New resistance level is the maximum value of the last 'adjusted_lookback' periods
                new_level = lookback_data['High'].max()
            elif lookback_data['cross_type'].iloc[-1] == 1:
                # New support level is the minimum value of the last 'adjusted_lookback' periods
                new_level = lookback_data['Low'].min()
            else:
                new_level = None
        else:
            new_level = None

        # Update the DataFrame
        dataframe.at[i, 'new_level'] = new_level

    return dataframe


def breakout_one(index="Russel"):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Report blocked stock")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    tickers_list = return_filtred_list(index=index)
    # Controlla se la lista dei ticker è vuota
    if not tickers_list:
        # Aggiungi un messaggio nel report o registra un log
        report.add_content("Nessun ticker soddisfa i criteri di selezione.")
        print("Nessun ticker soddisfa i criteri di selezione.")
    else:

        for item in tickers_list:
            result = True
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv",
                                   parse_dates=['Date'])
                ############################ enter macro strategy test here  ##################################
                # support_resistance_list = search_resistance_and_support_list
                #data = data.tail(120)
                finder = SupportResistanceFinder(data, n_clusters=5)
                support_resistance_levels, data = finder.find_levels(dynamic_cluster=False)
                # check if price broken resistance in last 3-5 period
                data = check_cross_levels(data, support_resistance_levels)
                # Verify if OC didn't broken resistence for 20 period but was near df[-25:-5]
                if data['cross_type'].iloc[-1] == 2:
                    data = check_pre_cross_break(data, level=data['crossed_level'].iloc[-1],
                                                 lookback_periods=data['cross_period_ago'].iloc[-1])
                elif data['cross_type'].iloc[-1] == 1:
                    data = check_pre_cross_break(data, level=data['crossed_level'].iloc[-1],
                                                 lookback_periods=data['cross_period_ago'].iloc[-1])
                else:
                    continue
                # check HH or LL
                if 'isPivot' not in data.columns:
                    add_pivot = PivotDetector(data)
                    data = add_pivot.add_pivot_column()
                else:
                    data = check_pivot_trends_with_sl(data)
                data.to_csv('/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/Data/tmp/tmp.csv')
                if data['cross_type'].iloc[-1] == 2 and pivot_high_trend:
                    # Gli ultimi 2 HH sono in aumento, utilizza lo stop loss calcolato
                    # SL = stop_loss
                    pass
                elif data['cross_type'].iloc[-1] == 1 and pivot_low_trend:
                    # Gli ultimi 2 LL sono in diminuzione, utilizza lo stop loss calcolato
                    # SL = stop_loss
                    pass
                else:
                    # Gestisci i casi in cui le condizioni di trend non sono soddisfatte o cross_type non è né 1 né 2
                    continue

                # verify break volume of breakout
                data = verify_breakout_volume(data)

                # Verify last 2-4 period resistance in not broken down
                data = check_inverse_cross(data)
                # define new resistance
                data = add_new_level_to_dataframe(data)
                # new_resistance is broken - Buy signal
                ###############################################################################################

                if result:
                    report.add_content(f'stock = {item} \n')
                    report.add_content(f'stock ={data["new_level"].iloc[-1]}\n')

            except FileNotFoundError:
                # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
                # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")

        # Salva il report e pulisci i file temporanei
    file_report = report.save_report(filename=f"{index}new")
    end_time = time.time()  # Registra l'ora di fine
    duration = end_time - start_time  # Calcola la durata totale

    print(f"Tempo di elaborazione {index}: {duration} secondi.")

    return file_report


if __name__ == '__main__':
    file_report = breakout_one()
    print(file_report)