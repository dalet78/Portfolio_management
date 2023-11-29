import pandas as pd
from Reports.image_builder import CandlestickChartGenerator

class StockBreakAnalyzer:
    def __init__(self, data, max_price=None):
        self.stock_name = data
        self.max_price = max_price
        self.data = pd.read_csv(f'Trading/Data/Daily/{data}_historical_data.csv')
        self.support_resistance_data = pd.read_csv(f'Trading/Data/SuppResist/{data}_SR.csv', skiprows=1, header=None, names=['Level', 'Weight']).set_index('Level')['Weight'].to_dict()
        self.image = CandlestickChartGenerator(self.data)

    def _analyze_last_price(self, threshold=0.02):
        last_price = self.data['Close'].iloc[-1]
        near_levels = []

        for level, weight in self.support_resistance_data.items():
            if self.max_price is not None and level > self.max_price:
                continue  # Ignora i livelli oltre il prezzo massimo
            
            if abs(last_price - level) / level <= threshold:
                near_levels.append((level, 'Support' if last_price > level else 'Resistance', weight))

        return near_levels

    def alert_near_levels(self):
        print(f"checking stock {self.stock_name}")
        near_levels = self._analyze_last_price()
        if near_levels:
            for level, level_type, weight in near_levels:
                content = f"Alert: Price near {level_type} level at {level} with weight {weight}"
                image = self.image.create_chart_with_horizontal_lines(lines=[level], max_points=30)
        else: 
            content= None
            image = None
        return content, image, self.data
    
    def _check_level_break(self, sessions=2):
        last_closes = self.data['Close'].iloc[-sessions:]
        breaks = []

        for level, weight in self.support_resistance_data.items():
            if self.max_price is not None and level > self.max_price:
                continue  # Ignora i livelli oltre il prezzo massimo

            if any(last_closes > level) and any(last_closes < level):
                level_type = 'Support' if last_closes.iloc[-1] > level else 'Resistance'
                breaks.append((level, level_type, weight))

        return breaks

    def alert_break_level(self):
        print(f"checking stock {self.stock_name}")
        break_levels = self._check_level_break()
        if break_levels:
            for level, level_type, weight in break_levels:
                content =f"Alert: Price break {level_type} level at {level} with weight {weight}"
                image = self.image.create_chart_with_horizontal_lines(lines=[level], max_points=30)
        else: 
            content= None
            image = None
        return content, image, self.data
    
    def clear_img_temp_files(self):
        self.image.clear_temp_files()


