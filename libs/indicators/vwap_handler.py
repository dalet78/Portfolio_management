import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta


class TradingVWAP:
    def __init__(self, data):
        """
        Initialize with a dataframe containing at least 'price', 'volume' columns.
        """
        self.data = data

    def calculate_vwap(self, timeframe='D'):
        """
        Calculate VWAP for a given timeframe using pandas_ta.
        """
        df = self.data.copy()
        df.set_index(pd.to_datetime(df['Date']), inplace=True)

        # Calcola il VWAP usando pandas_ta
        vwap = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])

        # Resample per il periodo specificato e calcola l'ultimo VWAP per quel periodo
        resampled_vwap = vwap.resample(timeframe).last()
        return resampled_vwap

    def calculate_rolling_std_deviation(self, vwap_series, window=5):
        """
        Calculate the rolling standard deviation for a given VWAP series.
        """
        rolling_std_dev = vwap_series.rolling(window=window).std()
        return rolling_std_dev

    def build_tuples(self, timeframe, window, last_n):
        """
        Build tuples of the last 'n' values for a given timeframe,
        including the rolling standard deviation.
        """
        vwap = self.calculate_vwap(timeframe)
        rolling_std_dev = self.calculate_rolling_std_deviation(vwap, window=window)

        tuples_list = []
        for i in range(-last_n, 0):
            tuples_list.append((vwap.iloc[i], rolling_std_dev.iloc[i]))

        return tuples_list

    def get_previous_friday_vwap_and_std(self):
        """
        Get the average VWAP of the last week up to the last Friday and the standard deviation of the sessions of that week.
        """
        vwap = self.calculate_vwap('D')  # Ensure daily VWAP calculation
        vwap.sort_index(inplace=True)

        # Find the index of the last Friday
        today = datetime.now()
        last_friday = today - timedelta(days=(today.weekday() - 4) % 7 + 7)
        start_of_week = last_friday - timedelta(days=last_friday.weekday())  # Monday of the week of the last Friday

        # Print the dates for debugging
        print(f"Inizio della settimana (lunedì): {start_of_week.date()}")
        print(f"Ultimo venerdì considerato: {last_friday.date()}")
        # Filter for the VWAP of the last week up to last Friday
        # Ensure the conditions are enclosed in parentheses
        last_week_vwap_series = vwap[
            (vwap.index.date >= start_of_week.date()) & (vwap.index.date <= last_friday.date())]
        average_last_week_vwap = last_week_vwap_series.mean() if not last_week_vwap_series.empty else np.nan

        # Calculate the standard deviation for the VWAP values of the last week
        last_week_std = last_week_vwap_series.std() if not last_week_vwap_series.empty else np.nan

        return average_last_week_vwap, last_week_std

    def get_last_month_vwap_and_std(self):
        """
        Get the average VWAP of the previous month and the standard deviation of the sessions of that month.
        """
        vwap = self.calculate_vwap('D')  # Ensure daily VWAP calculation
        vwap.sort_index(inplace=True)

        # Find the last day of the previous month
        today = datetime.now()
        first_day_of_this_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_this_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)

        # Filter the data to only include days from the last month
        last_month_vwap_series = vwap[
            (vwap.index.date >= first_day_of_last_month.date()) & (vwap.index.date <= last_day_of_last_month.date())]

        # Calculate the average VWAP for the previous month
        average_last_month_vwap = last_month_vwap_series.mean() if not last_month_vwap_series.empty else np.nan

        # Calculate the standard deviation for the VWAP values of the last month
        last_month_std = last_month_vwap_series.std() if not last_month_vwap_series.empty else np.nan

        return average_last_month_vwap, last_month_std

    def get_last_quarter_vwap_and_std(self):
        """
        Get the average VWAP of the previous quarter and the standard deviation of the sessions of that quarter.
        """
        vwap = self.calculate_vwap('D')  # Ensure daily VWAP calculation
        vwap.sort_index(inplace=True)

        # Determine the last day of the previous quarter
        today = datetime.now()
        current_quarter = (today.month - 1) // 3 + 1
        first_day_of_current_quarter = datetime(today.year, 3 * current_quarter - 2, 1)
        last_day_of_previous_quarter = first_day_of_current_quarter - timedelta(days=1)
        first_day_of_previous_quarter = datetime(last_day_of_previous_quarter.year,
                                                 3 * ((last_day_of_previous_quarter.month - 1) // 3) + 1, 1)

        # Print the dates for debugging
        print(f"Primo giorno del quadrimestre precedente: {first_day_of_previous_quarter.date()}")
        print(f"Ultimo giorno del quadrimestre precedente: {last_day_of_previous_quarter.date()}")

        # Filter the data to include only the days from the previous quarter
        last_quarter_vwap_series = vwap[(vwap.index.date >= first_day_of_previous_quarter.date()) & (
                    vwap.index.date <= last_day_of_previous_quarter.date())]

        # Calculate the average VWAP for the previous quarter
        average_last_quarter_vwap = last_quarter_vwap_series.mean() if not last_quarter_vwap_series.empty else np.nan

        # Calculate the standard deviation for the VWAP values of the previous quarter
        last_quarter_std = last_quarter_vwap_series.std() if not last_quarter_vwap_series.empty else np.nan

        return average_last_quarter_vwap, last_quarter_std

    def get_last_year_vwap_and_std(self):
        """
        Get the VWAP of the last available day of the previous year and the standard deviation of the sessions of that year.
        """
        vwap = self.calculate_vwap('D')
        # Ensure the data is in order
        vwap.sort_index(inplace=True)

        # Find the last day of the previous year
        today = datetime.now()
        last_day_of_previous_year = datetime(today.year - 1, 12, 31)
        first_day_of_previous_year = datetime(today.year - 1, 1, 1)

        # Filter the data to include only the days from the previous year
        last_year_vwap_series = vwap[(vwap.index.date >= first_day_of_previous_year.date()) & (
                    vwap.index.date <= last_day_of_previous_year.date())]

        # Calculate the average VWAP for the previous year
        average_last_year_vwap = last_year_vwap_series.mean() if not last_year_vwap_series.empty else np.nan

        # Calculate the standard deviation for the VWAP values of the previous year
        last_year_std = last_year_vwap_series.std() if not last_year_vwap_series.empty else np.nan

        return average_last_year_vwap, last_year_std

    def get_last_5_daily_vwap_with_changes(self):
        """
        Get the last 5 daily VWAP values and their changes (differences).
        """
        vwap = self.calculate_vwap('D')  # Calculate the daily VWAP
        vwap.sort_index(inplace=True)

        # Initialize lists to store the last 5 VWAP values and changes
        last_5_vwap = []
        changes = []

        # Start from the last day and go backwards until you get 5 valid values
        for i in range(1, len(vwap) + 1):
            current_vwap = vwap.iloc[-i]
            if not np.isnan(current_vwap):
                # If the current VWAP is not nan, add it to the list
                last_5_vwap.append(current_vwap)
                if len(last_5_vwap) > 1:
                    # Calculate the change from the previous value
                    changes.append(current_vwap - last_5_vwap[-2])
                if len(last_5_vwap) == 5:
                    # If we have 5 values, stop the loop
                    break

        # Reverse the lists as we collected them in reverse order
        last_5_vwap.reverse()
        changes.reverse()

        return np.array(last_5_vwap), np.array(changes)

    def get_last_daily_vwap(self):
        """
        Get the last daily VWAP value and its standard deviation.
        """
        vwap = self.calculate_vwap('D')  # Calculate the daily VWAP
        vwap.sort_index(inplace=True)
    
        # Filter out NaN values and select the last session
        last_session_vwap = vwap.dropna().iloc[-1:]
    
        # Calculate standard deviation for the last session
        last_session_std = last_session_vwap.std()
    
        return last_session_vwap.iloc[0], last_session_std

# Example usage:

###############################################################################################################
###############################################################################################################
# ########################################## SETTIMANA ###########################################
# trading_vwap = TradingVWAP(data)
# last_friday_vwap, last_friday_std = trading_vwap.get_previous_friday_vwap_and_std()

# print("VWAP del venerdì precedente:", last_friday_vwap)
# print("Deviazione standard delle ultime 5 sessioni fino a venerdì:", last_friday_std)

# ########################################## MESE ###########################################
# last_day_vwap, last_month_std = trading_vwap.get_last_month_vwap_and_std()

# print("VWAP dell'ultimo giorno del mese precedente:", last_day_vwap)
# print("Deviazione standard delle sessioni di quel mese:", last_month_std)

# ########################################## Quadrimestre ###########################################
# last_day_vwap, last_quarter_std = trading_vwap.get_last_quarter_vwap_and_std()

# print("VWAP dell'ultimo giorno del quadrimestre precedente:", last_day_vwap)
# print("Deviazione standard delle sessioni di quel quadrimestre:", last_quarter_std)

# ########################################## Anno ###########################################
# last_day_vwap, last_year_std = trading_vwap.get_last_year_vwap_and_std()

# print("VWAP dell'ultimo giorno utile dell'anno precedente:", last_day_vwap)
# print("Deviazione standard delle sessioni di quell'anno:", last_year_std)

# ########################################## Giornalieri ###########################################
# last_5_vwap, changes = trading_vwap.get_last_5_daily_vwap_with_changes()

# print("Ultimi 5 valori VWAP giornalieri:", last_5_vwap)
# print("Variazioni dei VWAP giornalieri:", changes)

##########################################################################################################
##########################################################################################################

# Calculate and print the tuples for different timeframes
# Adjust the 'window' and 'last_n' parameters as needed for each timeframe.
# daily_tuples = trading_vwap.build_tuples('D', window=5, last_n=5)
# weekly_tuples = trading_vwap.build_tuples('W', window=3, last_n=3)
# monthly_tuples = trading_vwap.build_tuples('M', window=3, last_n=3)
# quarterly_tuples = trading_vwap.build_tuples('Q', window=3, last_n=3)
# annual_tuples = trading_vwap.build_tuples('A', window=3, last_n=3)

# print("Daily Tuples:", daily_tuples)
# print("Weekly Tuples:", weekly_tuples)
# print("Monthly Tuples:", monthly_tuples)
# print("Quarterly Tuples:", quarterly_tuples)
# print("Annual Tuples:", annual_tuples)
