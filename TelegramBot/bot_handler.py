import logging
from TelegramBot.bot_parameter import token, api_id, api_hash
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove
import json
from .bot_command import *
import subprocess

class CommandBot:
    def __init__(self):
        """Initialize the bot."""
        self.bot = Client("BOT", api_id=api_id, api_hash=api_hash, bot_token=token)
        self.user_states = {}
        self.bot.add_handler(MessageHandler(self.start_command, filters.command("start")))
        self.bot.add_handler(MessageHandler(self.cancel, filters.command("stop")))
        self.bot.add_handler(MessageHandler(self.help_command, filters.command("help")))
        self.bot.add_handler(CallbackQueryHandler(self.handle_callback))
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        # self.command = Bot_Option()

    def start(self) -> None:
        """Start the bot."""
        self.logger.info("Starting bot")
        self.bot.run()

    def create_level_menu(self, menu="top"):
        # Creazione dei bottoni per il menu principale
        if menu == 'specialtool':
            keyboard = [
                [InlineKeyboardButton("TBD1", callback_data="action_buildsuppres"),
                 InlineKeyboardButton("TBD2", callback_data="action_option2")],
                [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]
            ]
        elif menu == 'updatedatabase':
            keyboard = [
                [InlineKeyboardButton("Update daily", callback_data="action_updatedaily"),
                 InlineKeyboardButton("update weekly", callback_data="action_updateweekly")],
                [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]
            ]
        elif menu == 'catchtrade':
            keyboard = [
                [InlineKeyboardButton("find blocked stock", callback_data="action_findblockedstock"),
                 InlineKeyboardButton("find lateral move", callback_data="action_findlateralmov")],
                [InlineKeyboardButton("method 3", callback_data="action_option_3"),
                 InlineKeyboardButton("method 4", callback_data="action_option_4")],
                [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]
            ]
        elif menu == 'macrotool':
            keyboard = [
                [InlineKeyboardButton("Update data", callback_data="action_updatemacrodata"),
                 InlineKeyboardButton("Download report", callback_data="action_downloadmacroreport")],
                [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("Update Database", callback_data="menu_updatedatabase"),
                 InlineKeyboardButton("Catch trading", callback_data="menu_catchtrade")],
                [InlineKeyboardButton("Macroeconomic tool", callback_data="menu_macrotool"),
                 InlineKeyboardButton("Special Tool", callback_data="menu_specialtool")]
            ]
        return InlineKeyboardMarkup(keyboard)

    @Client.on_message(filters.command("start"))
    def start_command(self, client, message):
        welcome_text = "Welcome, choose an option:"
        reply_markup = self.create_level_menu()
        message.reply_text(welcome_text, reply_markup=reply_markup)

    @Client.on_callback_query()
    def handle_callback(self, client, callback_query: CallbackQuery):
        data = callback_query.data

        if data.startswith("menu_"):
            new_menu = self.create_level_menu(menu=data.split("_")[1])
            current_text = callback_query.message.text

            if current_text != "Choose an option:" or callback_query.message.reply_markup != new_menu:
                callback_query.message.edit_text("Choose an option:", reply_markup=new_menu)
            else:
                self.logger.error(f'menu dont found {data.split("_")[1]}')
        # Verifica se il callback è per eseguire un'azione
        elif data.startswith("action_"):
            self.perform_action(client,callback_query, data.split("_")[1])

    def perform_action(self, client, callback_query, action):
        if action == "updatedaily":
            download_data_daily()
            callback_query.message.reply_text("Download daily data finish!")
        elif action == "updateweekly":
            download_data_weekly()
            callback_query.message.reply_text("Download weekly data finish!")
        elif action == "findblockedstock":
            try:
                file_report = blocked_stock()
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")
        elif action == "findlateralmov":
            try:
                file_report = find_lateral_mov()
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")

    def send_generated_pdf(self, client, chat_id, file_path):
        # Invia il PDF generato al client
        client.send_document(chat_id, file_path)

    @Client.on_message(filters.command("stop"))
    def cancel(self, client, message):
        """Cancel the conversation and remove the keyboard."""
        reply_text = 'Okay, bye.'
        reply_markup = ReplyKeyboardRemove()
        message.reply_text(reply_text, reply_markup=reply_markup)

    # def save_user_state(user_id, state):
    #     with open('user_states.json', 'r+') as file:
    #         data = json.load(file)
    #         data[str(user_id)] = state
    #         file.seek(0)
    #         json.dump(data, file)

    # def get_user_state(self, user_id):
    #     return self.user_states.get(user_id, TOP_LEVEL)

    def set_user_state(self, user_id, state):
        self.user_states[user_id] = state

    @Client.on_message(filters.command("help"))
    def help_command(self, client, message):
        help_text = """
        How you can use this bot:
        /start - Start the bot
        /help - Show this help message
        /cancel - Close the bot
        """
        message.reply_text(help_text)

    def start_conversation(self, message, id, SUB_MENU_1, reply_text, reply_keyboard):
        pass

if __name__ == '__main__':
    bot = CommandBot()
    bot.start()