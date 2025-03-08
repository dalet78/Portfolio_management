import threading
from TelegramBot.commander.download_data import download_data
from TelegramBot.bot_handler import CommandBot




if __name__ == '__main__':
    # download_thread = threading.Thread(target=download_data)
    # download_thread.start()

    bot = CommandBot()
    bot.start()