import json
import pandas as pd
from Trading.methodology.download_data.download_data_yahoo import StockDataDownloader
from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
from Trading.methodology.blocked_stock.blocked_stock import TradingAnalyzer
from Trading.methodology.lateral_movement.search_type_mov import TrendMovementAnalyzer


source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
def download_data_weekly():
    with open( f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
    # Lista dei ticker
    tickers_list = list(tickers.keys())
    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list, interval='1wk')
    downloader.download_data()

def download_data_daily():
    with open(f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)

    # Lista dei ticker
    tickers_list = list(tickers.keys())

    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list)
    downloader.download_data()
    stop_downloading()

def blocked_stock():
    report = ReportGenerator()
    report.add_title(title="Report blocked stock")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    # for strategy in param_data['Strategies']:
    #     if strategy['name'] == "breakout_lateral_move_second":
    #         parameters_dict = strategy['parameters']
    #         break
    with open(f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
        tickers_list = list(tickers.keys())

    for item in tickers_list:
        data = pd.read_csv(f"{source_directory}/Trading/Data/Daily/{item}_historical_data.csv", parse_dates=['Date'])
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


def find_lateral_mov():
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
            result = enhanced_strategy.evaluate_trend_and_laterality( lateral_check_method="ADX")
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