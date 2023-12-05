
import time, json
from Trading.methodology.download_data.download_data_yahoo import StockDataDownloader
source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"

with open(f"{source_directory}/json_files/russell2000.json", 'r') as file:
    tickers = json.load(file)

    # Lista dei ticker
tickers_list = list(tickers.keys())

# Utilizzo della classe StockDataDownloader
downloader = StockDataDownloader(tickers_list, index="Russel")
downloader.download_data()
