import os
from datetime import datetime
from support.logger import Logger ,LoggerSingleton
from libs.ibs_menager import IBOrderManager
from libs.tws_luncher import TWSLauncher
from framework.wait_start_session import wait_for_precise_time
from configuration import data_configuration_session
from framework.trading_daily_session import TradingLoopManager
from support.logger import LoggerSingleton

def start_trading(bot_instance, ib_manager):
    log = LoggerSingleton.get_logger()
    wait_for_precise_time()

    manager = TradingLoopManager(ib_manager=ib_manager)
    manager.telegram_bot = bot_instance
    closing_triggered = False

    while True:
        now = datetime.now()
        current_time = now.time()
        end_session = data_configuration_session.END_SESSION
        time_left = datetime.combine(now.date(), end_session) - now

        if time_left.total_seconds() <= 600 and not closing_triggered:
            log.log("🛑 Closing all positions before end of session", level="info")
            manager._close_all_positions()
            closing_triggered = True

        if current_time >= end_session:
            break

        manager.trading_loop()

    summary = ib_manager.get_daily_trade_summary_with_pnl()

    if bot_instance:
        bot_instance.send_telegram_message(summary)

if __name__ == "__main__":
    daily_date = datetime.now().strftime("%d_%m_%y__%H_%M")
    log_path = f"/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/daily_tading_{daily_date}.log"
    log = LoggerSingleton.get_logger(log_path)

    tws_path = os.path.expanduser("~/Jts/tws")
    username = "hcuckr695"
    password = "IlanaQ!W@e3r4t5"

    tws = TWSLauncher(tws_path, username, password)
    tws.start_tws()

    if not tws.wait_until_tws_ready(timeout=600):
        log.error("❌ Impossibile continuare: TWS non disponibile.")
        exit(1)

    ib_manager = IBOrderManager()
    from TelegramBot.bot_handler import CommandBot
    bot = CommandBot()
    bot.start()
    start_trading(bot, ib_manager)




