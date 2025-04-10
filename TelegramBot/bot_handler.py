import asyncio
import threading
import time
import logging
import os
import schedule

from support.logger import LoggerSingleton
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove
from libs.tws_luncher import TWSLauncher
from TelegramBot.commander import download_data, routine_commander
# from configuration import hours_configuration
from TelegramBot.bot_parameter import token, api_id, api_hash
from main_trading import start_trading
from libs.ibs_menager import IBOrderManager


class CommandBot:
    def __init__(self):
        """Initialize the bot."""
        self.bot = Client("BOT", api_id=api_id, api_hash=api_hash, bot_token=token)
        self.user_states = {}
        self.session_lock = threading.Lock()
        self.logger = LoggerSingleton.get_logger()

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.lista_chat_id = ['1458740893', '5634630295', '6948150159']

        # Schedule daily, weekly routines
        # schedule.every().day.at(hours_configuration.FIVE_MIN_HOUR_SEND_REPORT).do(
        #     routine_commander.routine, bot_instance=self, interval_type="5m"
        # )
        # schedule.every().day.at(hours_configuration.DAILY_HOUR_SEND_REPORT).do(
        #     routine_commander.routine, bot_instance=self, interval_type="Daily"
        # )
        # schedule.every().monday.at(hours_configuration.WEEKLY_HOUR_SEND_REPORT).do(
        #     routine_commander.routine, bot_instance=self, interval_type="weekly"
        # )

        # Add command handlers
        self.bot.add_handler(MessageHandler(self.start_command, filters.command("start")))
        self.bot.add_handler(MessageHandler(self.cancel, filters.command("stop")))
        self.bot.add_handler(MessageHandler(self.help_command, filters.command("help")))
        self.bot.add_handler(CallbackQueryHandler(self.handle_callback))

    def run_scheduler(self):
        """Run the scheduler in a separate thread."""
        while True:
            schedule.run_pending()
            time.sleep(60)

    def start(self):
        """Start the bot."""
        self.logger.log(message="Starting bot", level="info")
        self.bot.run()

    def create_level_menu(self, menu="top"):
        """Create inline keyboard menu."""
        menus = {
            'specialtool': [[InlineKeyboardButton("TBD1", callback_data="action_buildsuppres"),
                             InlineKeyboardButton("TBD2", callback_data="action_option2")],
                            [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]],
            'downloaddata': [[InlineKeyboardButton("Download Daily", callback_data="action_updatedaily"),
                              InlineKeyboardButton("Download Weekly", callback_data="action_updateweekly")],
                             [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]],
            'top': [[InlineKeyboardButton("Stock", callback_data="menu_catchtrade"),
                     InlineKeyboardButton("Download", callback_data="menu_downloaddata")],
                    [InlineKeyboardButton("Start TWS", callback_data="action_starttws"),
                     InlineKeyboardButton("Start Daily Session", callback_data="action_startdailysession")]
            ]
        }
        return InlineKeyboardMarkup(menus.get(menu, menus['top']))

    def start_command(self, client, message):
        """Handle /start command."""
        message.reply_text("Welcome, choose an option:", reply_markup=self.create_level_menu())

    def handle_callback(self, client, callback_query: CallbackQuery):
        """Handle button callbacks."""
        data = callback_query.data

        if data.startswith("menu_"):
            menu = data.split("_")[1]
            callback_query.message.edit_text("Choose an option:", reply_markup=self.create_level_menu(menu))
        elif data.startswith("action_"):
            self.perform_action(client, callback_query, data.split("_")[1])

    def perform_action(self, client, callback_query, action):
        """Execute actions based on button callbacks."""
        action_map = {
            "updatedaily": (self.handle_data_download, "daily"),
            "updateweekly": (self.handle_data_download, "weekly"),
            "startdailysession": (self.start_daily_session,),
            "starttws": (self.start_tws,)
        }

        if action in action_map:
            func, *args = action_map[action]
            func(client, callback_query, *args)
        else:
            callback_query.message.reply_text("Unrecognized action!")

    def start_daily_session(self, client, callback_query):
        self.logger.log(message="Starting daily session", level="info")

        def safe_main_trading(*args):
            try:
                asyncio.set_event_loop(asyncio.new_event_loop())

                # ✅ Istanzia IBOrderManager **dentro il thread**
                ib_manager = IBOrderManager()

                start_trading(bot_instance=self, ib_manager=ib_manager)
            except Exception as e:
                self.logger.log(message=f"Error in thread: {e}", level="error")

        with self.session_lock:
            thread = threading.Thread(target=safe_main_trading, daemon=True)
            thread.start()

        callback_query.message.reply_text("Daily session started!")

    def start_tws(self, client, callback_query, max_retries=5, wait_time=10, initial_wait=60):
        """Avvia TWS e verifica la connessione prima di inviare il messaggio di conferma."""
        tws_path = os.path.expanduser("~/Jts/tws")
        username = "hcuckr695"
        password = "IlanaQ!W@e3r4t5"

        tws = TWSLauncher(tws_path, username, password)
        tws.start_tws()

        time.sleep(initial_wait)

        # ✅ Inizializza solo una volta
        ib_manager = IBOrderManager()

        for attempt in range(1, max_retries + 1):
            if ib_manager.is_connected():
                callback_query.message.reply_text("✅ TWS successfully started and connected to IBKR!")
                return

            self.logger.log(message=f"Tentativo {attempt}: IB non ancora connesso, riprovo tra {wait_time}s...", level="warning")
            time.sleep(wait_time)

        callback_query.message.reply_text("❌ Error: Unable to connect to TWS after multiple attempts.")

    def handle_data_download(self, client, callback_query, period):
        """Download data for the specified period."""
        if period == "daily":
            download_data.download_data_daily()
        elif period == "weekly":
            download_data.download_data_weekly()
        callback_query.message.reply_text(f"Download {period} data finished!")

    def cancel(self, client, message):
        """Handle /stop command."""
        message.reply_text('Okay, bye.', reply_markup=ReplyKeyboardRemove())

    def help_command(self, client, message):
        """Handle /help command."""
        help_text = """
        Commands:
        /start - Start the bot
        /help - Show help message
        /stop - Stop the bot
        """
        message.reply_text(help_text)

    def send_telegram_message(self, text):
        """Invia un messaggio Telegram a tutti gli utenti configurati."""
        for chat_id in self.lista_chat_id:
            try:
                self.bot.send_message(chat_id=chat_id, text=text)
            except Exception as e:
                self.logger.log(message=f"❌ Error sending Telegram message to {chat_id}: {e}", level="error")


if __name__ == '__main__':
    bot = CommandBot()
    bot.start()
