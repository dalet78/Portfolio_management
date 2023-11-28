import json
import os
from portfolio_management.Trading.methodology.SuppRes.SR_construction import StockAnalysis
from portfolio_management.Trading.methodology.SuppRes.SR_break_advisor import StockBreakAnalyzer
from portfolio_management.Reports.report_builder import ReportGenerator


def create_support_resistance():
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "../../json_files/SP500-stock.json"), 'r') as file:
        tickers = json.load(file)

# Lista dei ticker
    tickers_list = list(tickers.keys())

    for item in tickers_list:
        stock_analysis = StockAnalysis(f"{item}")
        stock_analysis.update_pivot_data()

def breaker_analyzer(max_price= None):
    report= ReportGenerator()
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "../../json_files/SP500-stock.json"), 'r') as file:
        tickers = json.load(file)
    tickers_list = list(tickers.keys())
    report.add_title(title="Resistence and Support Breaks")

    for item in tickers_list:
        stock_analysis = StockBreakAnalyzer(f"{item}", max_price= max_price)
        content, image, df = stock_analysis.alert_break_level()
        if content and image  is not None:
            report.add_content(f"stock = {item}")
            report.add_commented_image(df, comment= content, image_path= image)
    
    report.save_report(filename="Report_RS_break")
    stock_analysis.clear_img_temp_files()

def near_breaker_analyzer(max_price= None):
    report= ReportGenerator()
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "../../json_files/SP500-stock.json"), 'r') as file:
        tickers = json.load(file)
    tickers_list = list(tickers.keys())
    report.add_title(title="Resistence and Support near breaks analisys")

    for item in tickers_list:
        stock_analysis = StockBreakAnalyzer(f"{item}", max_price= max_price)
        content, image, df =  stock_analysis.alert_near_levels()
        if content and image  is not None:
            report.add_content(f"stock = {item}")
            report.add_commented_image(df, comment= content, image_path= image)
    
    report.save_report(filename="Report_RS_near_break")
    stock_analysis.clear_img_temp_files()

if __name__ == "__main__":
    near_breaker_analyzer(max_price= 50)
    # comment