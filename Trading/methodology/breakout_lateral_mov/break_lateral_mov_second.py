import pandas as pd
import json
from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator

class BreakoutSignalAnalyzer_lateral_move_second:
    def __init__(self, data, params):
        """
        Inizializza la classe con il DataFrame, la percentuale per il range e il minimo numero di periodi.
        :param df: DataFrame contenente i dati storici degli stock.
        :param percentage: Percentuale per definire l'intervallo di prezzo.
        :param min_periods: Numero minimo di periodi per cui lo stock deve stare nel range.
        """
        self.df = data
        self.percentage = params["percentage"]
        self.min_periods = params["min_periods"]
        self.image = CandlestickChartGenerator(self.df)

    def analyze_range(self):
        """
        Analizza il DataFrame per identificare i periodi in cui lo stock è nel range.
        :return: Tuple con segnale, contenuto testuale e immagine.
        """
        content = None
        image = None
        signal = 0.0

        # Calcolo della variazione percentuale
        penultimate_price = self.df.iloc[-2]['Close']
        reference_price = self.df.iloc[-2-self.min_periods:-2]['Close'].mean()
        price_change_percentage = ((penultimate_price - reference_price) / reference_price) * 100

        if abs(price_change_percentage) > self.percentage:
            return signal, content, image

        # Definizione del range e calcolo della serie booleana per l'intero DataFrame
        self.df['Upper Bound'] = self.df['Close'] * (1 + self.percentage / 100)
        self.df['Lower Bound'] = self.df['Close'] * (1 - self.percentage / 100)
        in_range = (self.df['Low'] >= self.df['Lower Bound']) & (self.df['High'] <= self.df['Upper Bound'])

        # Filtra il DataFrame per gli ultimi 'min_periods'
        recent_df = self.df.iloc[-self.min_periods:]

        # Applica la condizione 'in_range' a questo DataFrame recente
        recent_in_range = recent_df[in_range.iloc[-self.min_periods:].values]
        
        # Conteggio dei periodi in range
        periods_in_range = recent_in_range.sum()

        # Calcola i prezzi massimi e minimi durante l'ultimo periodo di range
        max_price = recent_in_range['High'].max()
        min_price = recent_in_range['Low'].min()

        # Determinazione del segnale di trading
        last_price = self.df.iloc[-1]['Close']
        if last_price > self.df['Upper Bound'].iloc[-1]:
            content = (f"Buy signal - periods_in_range: {periods_in_range} \n"
                       f"max_price_in_range: {max_price}, min_price_in_range: {min_price}")
            image = self.image.create_chart_with_more_horizontal_lines(lines=[max_price, min_price], max_points=50)
            signal = 1.0  # Segnale di buy
        elif last_price < self.df['Lower Bound'].iloc[-1]:
            content = (f"Sell signal - periods_in_range: {periods_in_range} \n"
                       f"max_price_in_range: {max_price}, min_price_in_range: {min_price}")
            image = self.image.create_chart_with_more_horizontal_lines(lines=[max_price, min_price], max_points=50)
            signal = -1.0  # Segnale di sell

        return  signal , content, image
   
    def clear_img_temp_files(self):
        self.image.clear_temp_files()

#Example usage with the same mock data as before
parameters_dict = {}
report= ReportGenerator()
report.add_title(title="Lateral movement breaks analisys second")

with open("Trading/methodology/strategy_parameter.json", 'r') as file:
    param_data = json.load(file)

for strategy in param_data['Strategies']:
    if strategy['name'] == "breakout_lateral_move_second":
        parameters_dict = strategy['parameters']
        break
with open("json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
        tickers_list = list(tickers.keys())

for item in tickers_list:
    data = pd.read_csv(f"Trading/Data/Daily/{item}_historical_data.csv")
    enhanced_strategy = BreakoutSignalAnalyzer_lateral_move_second(data, parameters_dict)
    enhanced_signals, content, image = enhanced_strategy.analyze_range()
    if enhanced_signals != 0.0: 
            report.add_content(f"stock = {item}")
            report.add_commented_image(data, comment= content, image_path= image)
    print(f"checked stock {item}" )
report.save_report(filename="Report_lateral_mov_break_second")
enhanced_strategy.clear_img_temp_files()
    
    # print(f"for stock : {item} signal = {enhanced_signals}")  # Display the last few rows to see the signals and adjusted prices

