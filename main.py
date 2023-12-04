import schedule
import time, json
import threading
from TelegramBot.bot_handler import CommandBot
from Trading.methodology.download_data.download_data_yahoo import StockDataDownloader

source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
should_continue = True

def start_bot():
    bot = CommandBot()
    bot.start()

def download_data():
    global should_continue
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for day in days:
        schedule.every().day.at("04:00").do(download_data_daily)

    schedule.every().monday.at("05:00").do(download_data_weekly)
    while should_continue:
        schedule.run_pending()
        time.sleep(60)

def download_data_daily():
    with open(f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)

    # Lista dei ticker
    tickers_list = list(tickers.keys())

    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list)
    downloader.download_data()
    stop_downloading()

def download_data_weekly():
    with open( f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
    # Lista dei ticker
    tickers_list = list(tickers.keys())
    # Utilizzo della classe StockDataDownloader
    downloader = StockDataDownloader(tickers_list, interval='1wk')
    downloader.download_data()
    stop_downloading()

def stop_downloading():
    global should_continue
    should_continue = False

if __name__ == '__main__':
    download_thread = threading.Thread(target=download_data)
    download_thread.start()

    # Avvia il bot
    start_bot()

