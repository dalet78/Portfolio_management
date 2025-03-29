from datetime import datetime
from support.logger import Logger
from libs.ibs_menager import IBOrderManager
from framework.wait_start_session import wait_for_precise_time
from configuration import data_configuration_session
from framework.trading_daily_session import TradingLoopManager
from TelegramBot.bot_handler import bot

daily_date= datetime.now().strftime("%d_%m_%y")
log = Logger(f"/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/daily_tading_{daily_date}.log")

def start_trading():
    ib_manager = IBOrderManager()
    wait_for_precise_time(log=log)

    manager = TradingLoopManager(ib_manager=ib_manager, log=log)
    manager.telegram_bot = bot
    closing_triggered = False

    while True:
        now = datetime.now()
        current_time = now.time()
        end_session = data_configuration_session.END_SESSION
        time_left = datetime.combine(now.date(), end_session) - now

        if time_left.total_seconds() <= 600 and not closing_triggered:  # meno di 10 minuti
            log.log("🛑 Closing all positions before end of session", level="info")
            manager._close_all_positions()
            closing_triggered = True  # evita ripetizioni

        if current_time >= end_session:
            break

        manager.trading_loop()
    summary = ib_manager.get_daily_trade_summary_with_pnl()
    bot.send_telegram_message(summary)

if __name__ == "__main__":
    start_trading()




