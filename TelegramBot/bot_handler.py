import threading
import time
import logging
import subprocess
import schedule
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove

from TelegramBot.commander import download_data, routine_commander
from configuration import hours_configuration
from TelegramBot.bot_parameter import token, api_id, api_hash
from main_trading import start_trading


class CommandBot:
    def __init__(self):
        """Initialize the bot."""
        self.bot = Client("BOT", api_id=api_id, api_hash=api_hash, bot_token=token)
        self.user_states = {}
        self.session_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.lista_chat_id = ['1458740893', '5634630295']

        # Schedule daily, weekly routines
        schedule.every().day.at(hours_configuration.FIVE_MIN_HOUR_SEND_REPORT).do(
            routine_commander.routine, bot_instance=self, interval_type="5m"
        )
        schedule.every().day.at(hours_configuration.DAILY_HOUR_SEND_REPORT).do(
            routine_commander.routine, bot_instance=self, interval_type="Daily"
        )
        schedule.every().monday.at(hours_configuration.WEEKLY_HOUR_SEND_REPORT).do(
            routine_commander.routine, bot_instance=self, interval_type="weekly"
        )

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
        self.logger.info("Starting bot")
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
                    [InlineKeyboardButton("Macroeconomic tool", callback_data="menu_macrotool"),
                     InlineKeyboardButton("Start Daily Session", callback_data="action_startdailysession")]]
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
            "startdailysession": (self.start_daily_session,)
        }

        if action in action_map:
            func, *args = action_map[action]
            func(client, callback_query, *args)
        else:
            callback_query.message.reply_text("Unrecognized action!")

    def start_daily_session(self, client, callback_query):
        """Start daily trading session."""
        self.logger.info("Starting daily session")

        def safe_main_trading(*args):
            try:
                start_trading()  # Usa il nome corretto della funzione
            except Exception as e:
                self.logger.error(f"Error in thread: {e}", exc_info=True)

        with self.session_lock:
            thread = threading.Thread(target=safe_main_trading, args=(self, callback_query, "daily"), daemon=True)
            thread.start()

        callback_query.message.reply_text("Daily session started!")

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


if __name__ == '__main__':
    bot = CommandBot()
    bot.start()
