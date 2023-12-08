from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
import pandas as pd


class TradingAnalyzer:
    def __init__(self, dataset):
        """
        Initialize the TradingAnalyzer with a stock dataset.
        :param dataset: List of stock prices (float).
        """
        self.dataset = dataset
        self.image = CandlestickChartGenerator(self.dataset)

    def get_last_value(self, dataset_subset=None):
        """
        Get the last value from the dataset or a subset of it.
        :param dataset_subset: Optional subset of the dataset to consider. If None, uses the entire dataset.
        :return: The last stock price in the dataset or subset.
        """
        # Utilizza il subset del dataset se fornito, altrimenti utilizza l'intero dataset
        dataset_to_use = dataset_subset if dataset_subset is not None else self.dataset

        if not dataset_to_use.empty:
            return dataset_to_use["Close"].iloc[-1]
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

    def check_signal(self, period=30, use_previous_day=False):
        """
        Check if the stock price remains below resistance for more than 30 sessions and count how many times it touches or comes close to resistance within a 1% margin. Then do the opposite for support.
        If 'use_previous_day' is True, considers the dataset starting from the previous day.
        :param period: The number of periods to check.
        :param use_previous_day: Boolean to consider the dataset from the previous day.
        :return: A dictionary with details of price interactions with support and resistance.
        """
        dataset_to_use = self.dataset

        # Adjust the start index based on 'use_previous_day'
        start_index = -1 if use_previous_day else 0

        if len(dataset_to_use) < period:
            return False, None

        last_price = dataset_to_use['Close'][-1]
        support, resistance = self.calculate_support_resistance(last_price)

        consecutive_below_resistance = 0
        consecutive_above_support = 0
        max_consecutive_below_resistance = 0
        max_consecutive_above_support = 0
        touch_resistance_count = 0
        touch_support_count = 0

        for index in range(0, period):  # Adjust loop range
            open_price = dataset_to_use.Open[-period +index]
            high_price = dataset_to_use.High[-period +index]
            low_price = dataset_to_use.Low[-period +index]
            close_price = dataset_to_use.Close[-period +index]

            # Check for consecutive resistance interactions
            if resistance is not None and close_price <= resistance and open_price <= resistance:
                consecutive_below_resistance += 1
            else:
                max_consecutive_below_resistance = max(max_consecutive_below_resistance, consecutive_below_resistance)
                consecutive_below_resistance = 0

            # Check for consecutive support interactions
            if support is not None and close_price >= support and open_price>= support:
                consecutive_above_support += 1
            else:
                max_consecutive_above_support = max(max_consecutive_above_support, consecutive_above_support)
                consecutive_above_support = 0

            # Check for resistance and support touches
            if high_price >= resistance * 0.99 and high_price <= resistance:
                touch_resistance_count += 1
            if low_price <= support * 1.01 and low_price >= support:
                touch_support_count += 1

        interesting_below_resistance = max_consecutive_below_resistance >= period-3
        interesting_above_support = max_consecutive_above_support >= period-3

        if interesting_below_resistance :
            image = self.image.create_chart_with_horizontal_lines(lines=[resistance], max_points=period)
            result = {
                "status": interesting_below_resistance,
                "details":{
                    "resistence": resistance,
                    "position": "buy",
                    "below_resistance_count": touch_support_count,
                    "touch_resistance_count": touch_resistance_count,
                    "enter_price": resistance + 0.10,
                    "stop_loss": resistance - 0.20,
                    "take_profit":  resistance + 0.50
            }
            }
        elif interesting_above_support:
            image = self.image.create_chart_with_horizontal_lines(lines=[support], max_points=period)
            result = {
                "status": interesting_above_support,
                "details": {
                    "support": support,
                    "position": "sell",
                    "above_support_count": touch_support_count,
                    "touch_support_count": touch_support_count,
                    "enter_price": support - 0.10,
                    "stop_loss": support + 0.20,
                    "take_profit": support - 0.50
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
        enhanced_strategy = TradingAnalyzer(data)
        result, image = enhanced_strategy.check_signal()
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