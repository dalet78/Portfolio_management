from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
import pandas as pd
from libs.detectors.pivot_handler import PivotDetector
from libs.detectors.support_resistence_handler import SupportResistanceFinder
from libs.filtered_stock import return_filtred_list
import time


def check_cross_levels(dataframe, levels, use_ohlc=False):
    """
    Determine if there is a cross at the current point or between the previous close and the current open
    through any of the given levels and classify the type of cross:
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
        previous_close = dataframe.at[i - 1, 'Close']

        # Use OHLC data if specified
        if use_ohlc:
            current_high = dataframe.at[i, 'High']
            current_low = dataframe.at[i, 'Low']

        for level in levels:
            # Check for cross between current high/low or open/close
            if use_ohlc:
                crossed_upward = current_low < level <= current_high
                crossed_downward = current_high > level >= current_low
            else:
                crossed_upward = current_open < level <= current_close
                crossed_downward = current_open > level >= current_close

            # Check for cross between previous close and current open
            overnight_cross_upward = previous_close < level <= current_open
            overnight_cross_downward = previous_close > level >= current_open

            # Determine the cross type
            if crossed_upward or overnight_cross_upward:
                dataframe.at[i, 'cross_type'] = 2
                dataframe.at[i, 'crossed_level'] = level
                break
            elif crossed_downward or overnight_cross_downward:
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

def check_pre_cross_break(dataframe, check_periods=20, use_ohlc=True):
    """
    [Descrizione funzione aggiornata con correzioni]
    """
    dataframe['pre_cross_break'] = 0

    for i in range(1, len(dataframe)):
        cross_type = dataframe.at[i, 'cross_type']
        if cross_type != 0:
            level = dataframe.at[i, 'crossed_level']
            start_index = max(0, i - check_periods)
            pre_cross_data = dataframe.iloc[start_index:i]

            # Initialize variable to check for break
            break_occurred = False

            if use_ohlc:
                high = pre_cross_data['High']
                low = pre_cross_data['Low']
                previous_close = pre_cross_data['Close'].shift(1)

                # Check if level was broken during the day or overnight
                day_break = ((high > level) & (low < level))
                overnight_break = (((previous_close > level) & (dataframe.loc[start_index:i, 'Open'] < level)) |
                                   ((previous_close < level) & (dataframe.loc[start_index:i, 'Open'] > level)))

                break_occurred = (day_break | overnight_break).any()
            else:
                open_price = pre_cross_data['Open']
                close_price = pre_cross_data['Close']
                previous_close = pre_cross_data['Close'].shift(1)

                # Check if level was broken during the day or overnight
                day_break = (((open_price > level) & (close_price < level)) |
                             ((open_price < level) & (close_price > level)))
                overnight_break = ((previous_close > level) & (open_price < level)) | \
                                  ((previous_close < level) & (open_price > level))

                break_occurred = (day_break | overnight_break).any()

            # Update the DataFrame
            if break_occurred:
                dataframe.at[i, 'pre_cross_break'] = 1  # Level was broken
            else:
                dataframe.at[i, 'pre_cross_break'] = 2  # Level was not broken

    return dataframe

def verify_breakout_volume(dataframe, lookback_volume=10):
    """
    Check if the volume on the day of a cross is greater than 1.5 times the average volume of the last 'lookback_volume' days
    and if 'pre_cross_break' is equal to 2.

    :param dataframe: Pandas DataFrame with trading data containing 'cross_type', 'crossed_level', 'cross_period_ago', 'pre_cross_break', and 'Volume'.
    :param lookback_volume: Number of days to calculate the average volume, default is 10.
    :return: DataFrame with an updated 'verify_breakout_volume' column.
    """
    # Ensure the lookback period is not greater than the dataframe length
    lookback_volume = min(lookback_volume, len(dataframe))

    # Initialize the 'verify_breakout_volume' column
    dataframe['verify_breakout_volume'] = 0

    for i in range(len(dataframe)):
        # Proceed only if a cross occurred and pre_cross_break is 2
        if dataframe.at[i, 'cross_type'] != 0 and dataframe.at[i, 'pre_cross_break'] == 2:
            # Calculate the average volume for the lookback period
            start_index = max(0, i - lookback_volume)
            average_volume = dataframe.iloc[start_index:i]['Volume'].mean()

            # Get the volume on the day of the cross
            cross_volume = dataframe.at[i, 'Volume']

            # Compare and update the 'verify_breakout_volume' column
            if 1.5 * average_volume <= cross_volume < 2.2 * average_volume:
                dataframe.at[i, 'verify_breakout_volume'] = 1
            elif cross_volume >= 2.5 * average_volume:
                dataframe.at[i, 'verify_breakout_volume'] = 2

    return dataframe


def check_candle_body_relative_to_breakout(dataframe, body_threshold=0.7, lookback_volume=10):
    """
    Check if, for a breakout (type 2 for bullish and type 1 for bearish) with pre_cross_break equals 2,
    the candle's body is at least 'body_threshold' * 100% above (for bullish) or below (for bearish) the breakout line.

    :param dataframe: Pandas DataFrame with trading data containing 'Open', 'Close', 'cross_type', 'crossed_level', and 'pre_cross_break'.
    :param body_threshold: The percentage of the candle's body that must be above (for bullish) or below (for bearish) the breakout level. Default is 0.7.
    :param lookback_volume: Number of days to calculate the average volume, default is 10.
    :return: DataFrame with an updated 'candle_body_relative_to_breakout' column indicating the condition.
    """
    # Initialize the new column
    dataframe['candle_body_relative_to_breakout'] = False

    for i in range(len(dataframe)):
        cross_type = dataframe.at[i, 'cross_type']
        pre_cross_break = dataframe.at[i, 'pre_cross_break']

        if pre_cross_break == 2 and cross_type in [1, 2]:
            open_price = dataframe.at[i, 'Open']
            close_price = dataframe.at[i, 'Close']
            crossed_level = dataframe.at[i, 'crossed_level']
            body_size = abs(close_price - open_price)

            if cross_type == 2 and close_price > open_price:
                # Bullish breakout
                body_above_breakout = close_price - max(open_price, crossed_level)
                if body_above_breakout / body_size >= body_threshold:
                    dataframe.at[i, 'candle_body_relative_to_breakout'] = True

            elif cross_type == 1 and close_price < open_price:
                # Bearish breakout
                body_below_breakout = min(open_price, crossed_level) - close_price
                if body_below_breakout / body_size >= body_threshold:
                    dataframe.at[i, 'candle_body_relative_to_breakout'] = True

    return dataframe

# Apply the function to your dataframe
# updated_df = check_candle_body_relative_to_breakout(your_dataframe)


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

def round_to_half(number):
    # Arrotonda il numero alle migliaia per mantenere la precisione
    number = round(number, 3)
    # Estrai la parte intera e decimale
    integer_part = int(number)
    decimal_part = number - integer_part

    # Arrotonda la parte decimale a 0 o 0.5
    if decimal_part < 0.25:
        decimal_part = 0.0
    elif 0.25 <= decimal_part < 0.75:
        decimal_part = 0.5
    else:
        # Se la parte decimale è >= 0.75, arrotonda al prossimo numero intero
        decimal_part = 0.0
        integer_part += 1

    # Combina la parte intera e decimale arrotondata
    return integer_part + decimal_part


def breakout_finder(index="Russel"):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Possible breakout stock")

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
            print(f'Analyze stock = {item}')
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv",
                                   parse_dates=['Date'])
##############################################################################################
                finder = SupportResistanceFinder(data, n_clusters=5)
                support_resistance_levels, data = finder.find_levels(dynamic_cluster=False)
                support_resistance_levels= [round_to_half(num) for num in support_resistance_levels]
                data = check_cross_levels(data, support_resistance_levels, use_ohlc=True)
                data = check_pre_cross_break(data)
                data = verify_breakout_volume(data)
                data = check_candle_body_relative_to_breakout(data)

                result = False

                # Controlla ciascuna delle ultime 5 righe per vedere se almeno una soddisfa entrambe le condizioni
                for i in range(-1, -6, -1):  # Itera indietro dalle ultime 5 righe
                    if (data['verify_breakout_volume'].iloc[i] == 2 and
                            data['candle_body_relative_to_breakout'].iloc[i]):
                        result = True
                        image = CandlestickChartGenerator(data)
                        image_path = image.create_chart_with_horizontal_lines_and_volume(
                            lines=[data['crossed_level'].iloc[i]], max_points=90)
                        break

################################################################################################
                if result:
                    report.add_content(f'stock = {item} \n')
                    report.add_commented_image(df=data, comment=f'R/S ={data["crossed_level"].iloc[-1]}\n',
                                               image_path=image_path )

            except FileNotFoundError:
            # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
            # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")

        # Salva il report e pulisci i file temporanei
    file_report = report.save_report(filename=f"{index}_breakout_signal")
    end_time = time.time()  # Registra l'ora di fine
    duration = end_time - start_time  # Calcola la durata totale

    print(f"Tempo di elaborazione {index}: {duration} secondi.")

    return file_report

def fakeout_finder(index="Russel"):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Possible fakeout stock stock")

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
            print(f'Analyze stock = {item}')
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv",
                                   parse_dates=['Date'])
##############################################################################################
                finder = SupportResistanceFinder(data, n_clusters=5)
                support_resistance_levels, data = finder.find_levels(dynamic_cluster=False)
                data = check_cross_levels(data, support_resistance_levels, use_ohlc=True)
                data = check_pre_cross_break(data)
                data = verify_breakout_volume(data)
                data = check_candle_body_relative_to_breakout(data)

                result = False

                # Controlla ciascuna delle ultime 5 righe per vedere se almeno una soddisfa entrambe le condizioni
                for i in range(-1, -6, -1):  # Itera indietro dalle ultime 5 righe
                    if (data['verify_breakout_volume'].iloc[i] == 1):
                        result = True
                        image = CandlestickChartGenerator(data)
                        image_path = image.create_chart_with_horizontal_lines_and_volume(
                            lines=[data['crossed_level'].iloc[i]], max_points=90)
                        break

################################################################################################
                if result:
                    report.add_content(f'stock = {item} \n')
                    report.add_commented_image(df=data, comment=f'R/S ={data["crossed_level"].iloc[-1]}\n',
                                               image_path=image_path )

            except FileNotFoundError:
            # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
            # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")

        # Salva il report e pulisci i file temporanei
    file_report = report.save_report(filename=f"{index}_fakeout_signal")
    end_time = time.time()  # Registra l'ora di fine
    duration = end_time - start_time  # Calcola la durata totale

    print(f"Tempo di elaborazione {index}: {duration} secondi.")

    return file_report


if __name__ == '__main__':
    breakout_finder(index="SP500")
    breakout_finder(index="Russel")
    breakout_finder(index="Nasdaq")
    fakeout_finder(index="SP500")
    fakeout_finder(index="Russel")
    fakeout_finder(index="Nasdaq")
