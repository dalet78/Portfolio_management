from libs.download_data import StockDataDownloader
import json
import os

def download_data_daily():
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "json_files/SP500-stock.json"), 'r') as file:
        tickers = json.load(file)

# Lista dei ticker
    tickers_list = list(tickers.keys())

# Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list)
    downloader.update_data()

def download_data_weekly():
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "json_files/SP500-stock.json"), 'r') as file:
        tickers = json.load(file)

# Lista dei ticker
    tickers_list = list(tickers.keys())

# Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list, interval='1wk')
    downloader.update_data()
    
if __name__ == "__main__":
    download_data_daily()
    download_data_weekly()