from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
from Trading.methodology.lateral_movement.search_type_mov import TrendMovementAnalyzer
import json
import pandas as pd

class TradingLateralMovAnalyzer:
    def __init__(self, dataset, max_price=None):
        """
        Initialize the TradingAnalyzer with a stock dataset.
        :param dataset: List of stock prices (float).
        """
        self.dataset = dataset
        self.max_price = max_price
        self.image = CandlestickChartGenerator(self.dataset)

    def find_lateral_mov(self):
        report = ReportGenerator()
        report.add_title(title="Report blocked stock")

        with open("Trading/methodology/strategy_parameter.json", 'r') as file:
            param_data = json.load(file)

        with open("json_files/SP500-stock.json", 'r') as file:
            tickers = json.load(file)
            tickers_list = list(tickers.keys())

        for item in tickers_list:
            data = pd.read_csv(f"Trading/Data/Daily/{item}_historical_data.csv")
            enhanced_strategy = TrendMovementAnalyzer(data, max_price=50)
            result, image = enhanced_strategy.is_lateral_movement_percent()
            if result:
                print(f'stock = {item} -- FOUND ')
                report.add_content(f'stock = {item} ')
                report.add_commented_image(df=data, comment=f'Description = {result["details"]}', image_path=image)
            print(f"checked stock {item}")
        file_report = report.save_report(filename="Report_blocked_stock")
        enhanced_strategy.clear_img_temp_files()
        return file_report

if __name__ == '__main__':
    file_report = TradingLateralMovAnalyzer
    report= file_report.find_lateral_mov()
    print(report)