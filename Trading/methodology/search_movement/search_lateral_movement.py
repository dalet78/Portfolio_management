from Reports.report_builder import ReportGenerator
import json
import pandas as pd
from Trading.methodology.lateral_movement.search_type_mov import TrendMovementAnalyzer


def find_lateral_mov():
    report = ReportGenerator()
    report.add_title(title="Report blocked stock")

    with open("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    with open("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
        tickers_list = list(tickers.keys())

    for item in tickers_list:
        data = pd.read_csv(f"/Data/Daily/{item}_historical_data.csv")
        enhanced_strategy = TrendMovementAnalyzer(data, max_price=50)
        result, image = enhanced_strategy.is_lateral_movement_percent()
        if result:
            print(f'stock = {item} -- FOUND ')
            report.add_content(f'stock = {item} ')
            report.add_commented_image(df=data, image_path=image)
        print(f"checked stock {item}")
    file_report = report.save_report(filename="Report_stock_in_lateral_movement")
    enhanced_strategy.clear_img_temp_files()
    return file_report

if __name__ == '__main__':
    file_report = find_lateral_mov()
    print(file_report)