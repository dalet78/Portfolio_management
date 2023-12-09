import json
from libs.download_data.download_data_yahoo import StockDataDownloader



source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
def download_data_weekly():
    with open( f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
    # Lista dei ticker
    tickers_list = list(tickers.keys())
    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list, interval='1wk', index = "SP500")
    downloader.download_data()
    with open( f"{source_directory}/json_files/nasdaq.json", 'r') as file:
        tickers = json.load(file)
    # Lista dei ticker
    tickers_list = list(tickers.keys())
    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list, interval='1wk', index = "Nasdaq")
    downloader.download_data()
    with open( f"{source_directory}/json_files/russell2000.json", 'r') as file:
        tickers = json.load(file)
    # Lista dei ticker
    tickers_list = list(tickers.keys())
    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list, interval='1wk', index = "Russel")
    downloader.download_data()

def download_data_daily():
    with open(f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)

    # Lista dei ticker
    tickers_list = list(tickers.keys())

    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list, index = "SP500")
    downloader.download_data()
    with open( f"{source_directory}/json_files/nasdaq.json", 'r') as file:
        tickers = json.load(file)
    # Lista dei ticker
    tickers_list = list(tickers.keys())
    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list, index = "Nasdaq")
    downloader.download_data()
    with open( f"{source_directory}/json_files/russell2000.json", 'r') as file:
        tickers = json.load(file)
    # Lista dei ticker
    tickers_list = list(tickers.keys())
    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list, index = "Russel")
    downloader.download_data()

if __name__ == '__main__':
    download_data_daily()
