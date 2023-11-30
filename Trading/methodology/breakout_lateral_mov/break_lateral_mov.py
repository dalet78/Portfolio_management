import pandas as pd
import json
from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator

class BreakoutSignalAnalyzer_lateral_move:
    def __init__(self, data, params):
        """
        Inizializza la classe con i dati storici.
        :param data: DataFrame di Pandas con colonne 'High', 'Low', e 'Close'.
        :param window: Numero di periodi per calcolare la SMA e le Bande di Bollinger (default 20).
        :param num_of_std: Numero di deviazioni standard per le Bande di Bollinger (default 2).
        :param lateral_periods: Numero minimo di periodi consecutivi per identificare un movimento laterale (default 15).
        :param atr_threshold: Soglia dell'ATR per considerare il mercato a bassa volatilità (default 0.5).
        """
        self.data = data
        self.window = params["window"]
        self.num_of_std = params["num_of_std"]
        self.lateral_periods = params["lateral_periods"]
        self.atr_threshold = params["atr_threshold"]
        self.image = CandlestickChartGenerator(self.data)

    def BollingerBands(self):
        """ Calcola le Bande di Bollinger. """
        sma = self.data['Close'].rolling(window=self.window).mean()
        rstd = self.data['Close'].rolling(window=self.window).std()
        self.data['Upper Band'] = sma + self.num_of_std * rstd
        self.data['Lower Band'] = sma - self.num_of_std * rstd

    def ATR(self):
        """ Calcola l'Average True Range (ATR). """
        high_low = self.data['High'] - self.data['Low']
        high_close = (self.data['High'] - self.data['Close'].shift()).abs()
        low_close = (self.data['Low'] - self.data['Close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        self.data['ATR'] = true_range.rolling(window=self.window).mean()

    def detect_breakout(self):
        """
        Rileva se il movimento laterale è stato rotto e fornisce segnali di buy o sell.
        :return: Segnale di buy (1.0), sell (-1.0) o nessun segnale (0.0).
        """
        self.BollingerBands()
        self.ATR()
        lateral_count = 0
        signal = 0.0
        content = None
        image = None

        for index, row in self.data.iterrows():
            # Controlla se siamo in un movimento laterale
            if row['Low'] > row['Lower Band'] and row['High'] < row['Upper Band']: #and row['ATR'] < self.atr_threshold:
                lateral_count += 1
                if lateral_count >= self.lateral_periods:
                    # Controlla se il movimento laterale è stato rotto
                    if row['Close'] > row['Upper Band']:
                        content ="Buy signal"
                        image = self.image.create_chart_with_more_horizontal_lines(lines=[row['Upper Band'],row['Lower Band']], max_points=50)
                        signal = 1.0    
                    elif row['Close'] < row['Lower Band']:
                        content ="Sell signal"
                        image = self.image.create_chart_with_more_horizontal_lines(lines=[row['Upper Band'],row['Lower Band']], max_points=50)
                        signal = -1.0                  
            else:
                lateral_count = 0

        return signal, content, image  # Nessun segnale
    
    def clear_img_temp_files(self):
        self.image.clear_temp_files()

#Example usage with the same mock data as before
parameters_dict = {}
report= ReportGenerator()
report.add_title(title="Lateral movement breaks analisys")

with open("Trading/methodology/strategy_parameter.json", 'r') as file:
    param_data = json.load(file)

for strategy in param_data['Strategies']:
    if strategy['name'] == "breakout_lateral_move":
        parameters_dict = strategy['parameters']
        break
with open("json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
        tickers_list = list(tickers.keys())

for item in tickers_list:
    data = pd.read_csv(f"Trading/Data/Daily/{item}_historical_data.csv")
    enhanced_strategy = BreakoutSignalAnalyzer_lateral_move(data, parameters_dict)
    enhanced_signals, content, image = enhanced_strategy.detect_breakout()
    if enhanced_signals != 0.0: 
            report.add_content(f"stock = {item}")
            report.add_commented_image(data, comment= content, image_path= image)
    print(f"checked stock {item}" )
report.save_report(filename="Report_lateral_mov_break")
enhanced_strategy.clear_img_temp_files()
    
    # print(f"for stock : {item} signal = {enhanced_signals}")  # Display the last few rows to see the signals and adjusted prices

