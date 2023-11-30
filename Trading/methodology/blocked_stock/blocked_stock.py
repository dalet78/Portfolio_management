from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
import pandas as pd


class TradingAnalyzer:
    def __init__(self, dataset, max_price=None):
        """
        Initialize the TradingAnalyzer with a stock dataset.
        :param dataset: List of stock prices (float).
        """
        self.dataset = dataset
        self.max_price = max_price
        self.image = CandlestickChartGenerator(self.dataset)


    def get_last_value(self):
        """
        Get the last value from the dataset.
        :return: The last stock price.
        """
        if not self.dataset.empty:
            last_price = self.dataset["Close"].iloc[-1]
            return last_price if self.max_price is None or last_price <= self.max_price else None
        return None

    def calculate_support_resistance(self, price):
        """
        Calculate support and resistance levels based on the given price.
        :param price: The stock price.
        :return: A tuple of (support, resistance).
        """
        resistance = int(price) + 1 if price and not pd.isna(price) else None
        support = int(price) if price and not pd.isna(price) else None
        return support, resistance

    def check_price_range(self, period=60):
        """
        Check if the stock price remains below resistance for more than 30 sessions and count how many times it touches or comes close to resistance within a 1% margin. Then do the opposite for support.
        :param period: The number of periods to check.
        :return: A dictionary with details of price interactions with support and resistance.
        """
        if len(self.dataset) < period:
            return False

        last_price = self.get_last_value()
        support, resistance = self.calculate_support_resistance(last_price)

        below_resistance_count = 0
        touch_resistance_count = 0
        above_support_count = 0
        touch_support_count = 0

        for price in self.dataset["Close"][-period:]:
            if self.max_price is not None and pd.isna(price):
                continue

            if self.max_price is not None and price > self.max_price:
                continue

            # Checking for resistance interactions
            if resistance is not None and price < resistance:
                below_resistance_count += 1
                if resistance * 0.99 <= price <= resistance:
                    touch_resistance_count += 1

            # Checking for support interactions
            if support is not None and price > support:
                above_support_count += 1
                if support <= price <= support * 1.01:
                    touch_support_count += 1

        interesting_below_resistance = below_resistance_count >45 and touch_resistance_count > 3
        interesting_above_support = above_support_count > 45 and touch_support_count > 3

        if interesting_below_resistance :
            image = self.image.create_chart_with_horizontal_lines(lines=[resistance], max_points=90)
            result = {
                "status": interesting_below_resistance,
                "details":{
                    "resistence": resistance,
                    "below_resistance_count": below_resistance_count,
                    "touch_resistance_count": touch_resistance_count,
                }
            }
        elif interesting_above_support:
            image = self.image.create_chart_with_horizontal_lines(lines=[support], max_points=90)
            result = {
                "status": interesting_above_support,
                "details": {
                    "support": support,
                    "above_support_count": above_support_count,
                    "touch_support_count": touch_support_count
                }
            }
        else:
            result = False
            image = None
        return result, image

    def clear_img_temp_files(self):
        self.image.clear_temp_files()


def main():
    report = ReportGenerator()
    report.add_title(title="Report blocked stock")

    with open("Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    # for strategy in param_data['Strategies']:
    #     if strategy['name'] == "breakout_lateral_move_second":
    #         parameters_dict = strategy['parameters']
    #         break
    with open("json_files/SP500-stock.json", 'r') as file:
            tickers = json.load(file)
            tickers_list = list(tickers.keys())

    for item in tickers_list:
        data = pd.read_csv(f"Trading/Data/Daily/{item}_historical_data.csv")
        enhanced_strategy = TradingAnalyzer(data, max_price=50)
        result, image = enhanced_strategy.check_price_range()
        if result:
            print(f'stock = {item} -- FOUND ')
            report.add_content(f'stock = {item} ')
            report.add_commented_image(df=data, comment=f'Description = {result["details"]}', image_path=image)
        print(f"checked stock {item}")
    file_report = report.save_report(filename="Report_blocked_stock")
    enhanced_strategy.clear_img_temp_files()
    return file_report

if __name__ == '__main__':
    file_report = main()
    print(file_report)