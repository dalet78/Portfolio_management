import json
import schedule
import time
from libs.download_data.download_data_ibs import StockDataDownloader
from configuration import hours_configuration

import json

source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"

should_continue= True
# Implementa una funzione flessibile per scaricare i dati

def download_data():
    global should_continue
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for day in days:
        schedule.every().day.at(hours_configuration.DAILY_HOUR_DOWNLOAD).do(update_data())

    schedule.every().monday.at(hours_configuration.WEEKLY_HOUR_DOWNLOAD).do(update_data())
    while should_continue:
        schedule.run_pending()
        time.sleep(60)

def download_historical_data():
    with open(f"{source_directory}/json_files/list_companies.json", 'r') as file:
        tickers = json.load(file)

    # Lista dei ticker
    tickers_list = list(tickers.keys())

    # Utilizzo della classe StockDataDownloader
    # downloader = StockDataDownloader(tickers_list, index = "ALL" ).download_historical_data()
    # downloader = StockDataDownloader(tickers_list, interval="5m", index="ALL").download_historical_data()
    # downloader = StockDataDownloader(tickers_list, interval='1wk', index="ALL").download_historical_data()
    stop_downloading()

def update_data():
    with open(f"{source_directory}/json_files/list_companies.json", 'r') as file:
        tickers = json.load(file)

    # Lista dei ticker
    tickers_list = list(tickers.keys())
    downloader = StockDataDownloader(tickers_list, index="ALL").update_data()
    downloader = StockDataDownloader(tickers_list, interval="5m", index="ALL").update_data()
    downloader = StockDataDownloader(tickers_list, interval='1wk', index="ALL").update_data()
    stop_downloading()


def stop_downloading():
    global should_continue
    should_continue = False

if __name__ == '__main__':
    update_data( )

