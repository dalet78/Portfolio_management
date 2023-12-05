import pandas as pd
import json
from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator


class TrendMovementAnalyzer:
    def __init__(self, df, max_price=None):
        self.data = df
        if max_price is not None:
            self.data= self.data[self.data['Close'] <= max_price]
        self.image = CandlestickChartGenerator(self.data)

    def is_upward_trend_SMA(self, window=20, lookback_period=20, threshold=0.5):
        """
        Identify if moovemnte is upware.
        :param window: SMA period.
        :return: return boolean value if trand is upware.
        """
        self.data_copy = self.data.copy()
        if self.data_copy is None:
            print("Data not found.")
            return False, None

        # Verify that dataset contain close column
        if 'Close' not in self.data_copy.columns:
            print("Close column is not present.")
            return False, None

        # Calculate SMA
        self.data_copy['Moving_Average'] = self.data_copy['Close'].rolling(window=window).mean()

        # Determine if Close is above Moving Average
        self.data_copy['Above_MA'] = self.data_copy['Close'] > self.data_copy['Moving_Average']

        # Calculate the proportion of recent periods where Close is above MA
        recent_trend = self.data_copy['Above_MA'].iloc[-lookback_period:]
        upward_trend_proportion = recent_trend.sum() / len(recent_trend)
        is_trend_up= upward_trend_proportion >= threshold
        # if is_trend_up:
        #     image =self.image.create_chart_with_SMA(max_points=90

        return is_trend_up#, image

    def is_downward_trend_SMA(self, window=20, lookback_period=20, threshold=0.5):
        """
        Identify if moovemnte is downware.
        :param window: SMA period.
        :return: return boolean value if trand is upware.
        """
        self.data_copy = self.data.copy()
        if self.data_copy is None:
            print("Data not found.")
            return False, None

        # Verify that dataset contain close column
        if 'Close' not in self.data_copy.columns:
            print("Close column is not present.")
            return False, None

        # Calculate SMA
        self.data_copy['Moving_Average'] = self.data_copy['Close'].rolling(window=window).mean()

        # Determine if Close is above Moving Average
        self.data_copy['Above_MA'] = self.data_copy['Close'] < self.data_copy['Moving_Average']

        # Calculate the proportion of recent periods where Close is above MA
        recent_trend = self.data_copy['Above_MA'].iloc[-lookback_period:]
        downward_trend_proportion = recent_trend.sum() / len(recent_trend)
        is_trend_down = downward_trend_proportion >= threshold
        # if is_trend_down:
        #     image =self.image.create_chart_with_SMA(max_points=90)


        return is_trend_down #, image

    def _calculate_RSI(self, window=14):
        """
        Calcola l'indicatore Relative Strength Index (RSI).
        :param window: Numero di periodi da usare per calcolare l'RSI.
        :return: Serie RSI.
        """
        self.data_copy = self.data.copy()
        delta = self.data_copy['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def is_upward_trend_using_RSI(self, rsi_threshold=50, window=14):
        """
        Identify if moovement is upware  with RSI support.
        :param rsi_threshold: threshold for to verify if trend is up
        :param window: period number for to define RSI.
        :return: Bool, True if trend is up, False otherwise.
        """
        self.data_copy = self.data.copy()
        if self.data_copy is None:
            print("Data not found.")
            return False, None

        # RSI
        self.data_copy['RSI'] = self._calculate_RSI(window)

        # Verify if movement is upware
        is_trend_up = self.data_copy['RSI'] > rsi_threshold
        # if is_trend_up:
        #     image =self.image.create_chart_with_RSI(max_points=90)

        return is_trend_up#, image

    def is_downward_trend_using_RSI(self, rsi_threshold=50, window=14):
        """
        Identify if moovement is downware  with RSI support.
        :param rsi_threshold: threshold for to verify if trend is down
        :param window: period number for to devine RSI.
        :return: Bool, True if trend is down, False otherwise.
        """
        self.data_copy = self.data.copy()
        if self.data_copy is None:
            print("Data not found.")
            return False, None

        # RSI
        self.data_copy['RSI'] = self._calculate_RSI(window)

        # Verify if movement is downware
        is_trend_down = self.data_copy['RSI'] < rsi_threshold
        # if is_trend_down:
        #     image =self.image.create_chart_with_RSI(max_points=90)

        return is_trend_down#, image

    def _calculate_MACD(self, span_short=12, span_long=26, span_signal=9):
        """
        Calculates the Moving Average Convergence Divergence (MACD).
        :param span_short: Span for the short-term EMA.
        :param span_long: Span for the long-term EMA.
        :param span_signal: Span for the signal line.
        """
        self.data_copy['EMA_short'] = self.data_copy['Close'].ewm(span=span_short, adjust=False).mean()
        self.data_copy['EMA_long'] = self.data_copy['Close'].ewm(span=span_long, adjust=False).mean()
        self.data_copy['MACD'] = self.data_copy['EMA_short'] - self.data_copy['EMA_long']
        self.data_copy['Signal_Line'] = self.data_copy['MACD'].ewm(span=span_signal, adjust=False).mean()

    def is_upward_trend_using_MACD(self):
        """
        Determines if there is an upward trend using MACD.
        :return: Bool, True if there is an upward trend, False otherwise.
        """
        self.data_copy = self.data.copy()
        if self.data_copy is None:
            print("Data not loaded.")
            return False, None

        self._calculate_MACD()

        # Check if MACD is above the signal line
        is_trend_up = self.data_copy['MACD'].iloc[-1] > self.data_copy['Signal_Line'].iloc[-1]
        # if is_trend_up:
        #     image =self.image.create_chart_with_MACD(max_points=90)

        return is_trend_up#, image


    def is_downward_trend_using_MACD(self):
        """
        Determines if there is a downward trend using MACD.
        :return: Bool, True if there is a downward trend, False otherwise.
        """
        self.data_copy = self.data.copy()
        if self.data_copy is None:
            print("Data not loaded.")
            return False, None

        self._calculate_MACD()
        is_trend_down= self.data_copy['MACD'].iloc[-1] < self.data_copy['Signal_Line'].iloc[-1]
        # if is_trend_down:
        #     image =self.image.create_chart_with_MACD(max_points=90)

        return is_trend_down#, image

    def is_lateral_movement_bollinger_bands(self, window=20, num_std_dev=2, threshold_percentage=0.05):
        self.data_copy = self.data.copy()
        self.data_copy['SMA'] = self.data_copy['Close'].rolling(window=window).mean()
        self.data_copy['STD_DEV'] = self.data_copy['Close'].rolling(window=window).std()
        self.data_copy['Upper_Band'] = self.data_copy['SMA'] + (self.data_copy['STD_DEV'] * num_std_dev)
        self.data_copy['Lower_Band'] = self.data_copy['SMA'] - (self.data_copy['STD_DEV'] * num_std_dev)
     
        band_width = (self.data_copy['Upper_Band'] - self.data_copy['Lower_Band']) / self.data_copy['SMA']
        narrow_band = band_width < threshold_percentage
        max_streak = narrow_band.cumsum() - narrow_band.cumsum().where(~narrow_band).ffill().fillna(0).max()
        is_lateral = narrow_band.iloc[-1]
    
        return is_lateral, max_streak

    def calculate_ADX(self, window=14):
        # Calcolo delle differenze positive e negative
        self.data_copy['+DM'] = self.data_copy['High'].diff()
        self.data_copy['-DM'] = self.data_copy['Low'].diff()

        # Determina quali differenze devono essere considerate
        self.data_copy['+DM'] = self.data_copy.apply(lambda row: row['+DM'] if row['+DM'] > row['-DM'] and row['+DM'] > 0 else 0,
                                           axis=1)
        self.data_copy['-DM'] = self.data_copy.apply(lambda row: -row['-DM'] if row['-DM'] > row['+DM'] and row['-DM'] > 0 else 0,
                                           axis=1)

        # Shift the 'Close' column by one to get the previous value
        self.data_copy['Prev_Close'] = self.data_copy['Close'].shift()

        # Now apply your function
        self.data_copy['TR'] = self.data_copy.apply(lambda row: max(abs(row['High'] - row['Low']),
                                                          abs(row['High'] - row['Prev_Close']),
                                                          abs(row['Low'] - row['Prev_Close'])), axis=1)

        # Calcola gli indicatori direzionali lisciati
        self.data_copy['+DMI'] = self.data_copy['+DM'].rolling(window=window).mean() / self.data_copy['TR'].rolling(
            window=window).mean()
        self.data_copy['-DMI'] = self.data_copy['-DM'].rolling(window=window).mean() / self.data_copy['TR'].rolling(
            window=window).mean()

        # Calcola l'ADX
        self.data_copy['DX'] = (abs(self.data_copy['+DMI'] - self.data_copy['-DMI']) / (self.data_copy['+DMI'] + self.data_copy['-DMI'])) * 100
        self.data_copy['ADX'] = self.data_copy['DX'].rolling(window=window).mean()

    def is_lateral_movement_ADX(self, window=14, adx_threshold=25):
        """
        Determines if there is a lateral movement using the Average Directional Index (ADX).
        :param window: Number of periods for the ADX calculation.
        :return: Bool, True if there is a lateral movement, False otherwise.
        """
         self.data_copy = self.data.copy()
        self.calculate_ADX(window)
    
        if not self.data_copy['ADX'].empty:
            below_threshold = self.data_copy['ADX'] < adx_threshold
            max_streak = below_threshold.cumsum() - below_threshold.cumsum().where(~below_threshold).ffill().fillna(0).max()
            is_lateral = below_threshold.iloc[-1]
        else:
            print("ADX empty")
            return False, None
    
        return is_lateral, max_streak

    def is_lateral_movement_percent(self, last_periods=10, threshold=0.05):
        """
        Determines if there is a lateral movement based on the percentage change.
        :param window: Number of periods for calculating percentage change.
        :param threshold: Threshold for defining a lateral movement.
        :return: Bool, True if there is a lateral movement, False otherwise.
        """
        self.data_copy = self.data.copy()

        if self.data_copy is None or 'Close' not in self.data_copy.columns or len(self.data_copy) < last_periods:
            return False, None
    
        self.data_copy['Price_Change'] = self.data_copy['Close'].pct_change()
        cum_change = self.data_copy['Price_Change'].rolling(window=last_periods).sum().abs()
        lateral_periods = cum_change < threshold
        max_streak = lateral_periods.cumsum() - lateral_periods.cumsum().where(~lateral_periods).ffill().fillna(0).max()
        is_lateral = lateral_periods.iloc[-1]

        return is_lateral, max_streak

    def evaluate_trend_and_laterality(self, periods= [40], lateral_check_method="percent", lateral_threshold=0.05):
        """
        Valuta il trend (sia in salita che in discesa) e verifica se l'ultimo movimento è laterale.
        :param periods: Lista di periodi per le medie mobili.
        :param lateral_check_method: Metodo per controllare il movimento laterale ('percent', 'ADX', 'Bollinger').
        :param lateral_threshold: Soglia per il movimento laterale.
        :return: Dict con i risultati della valutazione del trend e del movimento laterale.
        """
        self.data_copy = self.data.copy()
        trend_results = {}
        for period in periods:
            trend_up = self.is_upward_trend_SMA(window=period)
            trend_down = self.is_downward_trend_SMA(window=period)

            if trend_up and not trend_down:
                trend_results[str(period)] = True
            elif trend_down and not trend_up:
                trend_results[str(period)] = True
            else:
                trend_results[str(period)] = False

        if lateral_check_method == "percent":
            lateral_movement = self.is_lateral_movement_percent(last_periods=periods[-1], threshold=lateral_threshold)
        elif lateral_check_method == "ADX":
            lateral_movement = self.is_lateral_movement_ADX(window=periods[-1], adx_threshold =lateral_threshold)
        elif lateral_check_method == "Bollinger":
            lateral_movement = self.is_lateral_movement_bollinger_bands(window=periods[-1],
                                                                        threshold_percentage=lateral_threshold)
        else:
            raise ValueError("Invalid lateral check method.")

        trend_results["Lateral Movement"] = True if lateral_movement else False
        overall_trend = all(trend_results.values())
        return overall_trend

    def create_tmp_image(self):
        return self.image.create_chart_with_SMA(max_points=90)

    def clear_img_temp_files(self):
        self.image.clear_temp_files()

def main():
    report = ReportGenerator()
    report.add_title(title="Report lateral movement")

    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    with open(f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
        tickers_list = list(tickers.keys())

    for item in tickers_list:
        data = pd.read_csv(f"{source_directory}/Trading/Data/Daily/{item}_historical_data.csv")
        if data["Close"].iloc[-1] < 50:
            enhanced_strategy = TrendMovementAnalyzer(data)
            image = CandlestickChartGenerator(data)
            result = enhanced_strategy.evaluate_trend_and_laterality()
            if result:
                image = image.create_simple_chart(max_points=50)
                print(f'stock = {item} -- FOUND ')
                report.add_content(f'stock = {item} ')
                report.add_commented_image(df=data, comment=f'Description', image_path=image)
            print(f"checked stock {item}")
        else:
            print(f"stock {item} is over price")
    file_report = report.save_report(filename="Report_lateral_movement")
    enhanced_strategy.clear_img_temp_files()
    return file_report

if __name__ == '__main__':
    file_report = main()
    print(file_report)
