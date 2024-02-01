import logging
from TelegramBot.bot_parameter import token, api_id, api_hash
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove
from .bot_command import *
import subprocess
from libs.detectors.crossing_RS_handler import breakout_finder, fakeout_finder
import schedule
import time

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
        # Pianifica l'esecuzione della routine giornaliera alle 8:00 ogni mattina
        schedule.every().day.at("11:19").do(self.daily_routine)
        schedule.every().tuesday.at("08:00").do(self.daily_routine)
        schedule.every().wednesday.at("08:00").do(self.daily_routine)
        schedule.every().thursday.at("08:00").do(self.daily_routine)
        schedule.every().friday.at("08:00").do(self.daily_routine)
        schedule.every().saturday.at("08:00").do(self.daily_routine)
        schedule.every().saturday.at("10:00").do(self.weekly_routine)
        self.lista_chat_id = ['1458740893','5634630295']

    def start(self) -> None:
        """Start the bot."""
        self.logger.info("Starting bot")
        self.bot.run()

    def daily_routine(self):
        # Logica della tua routine quotidiana qui
        # Ad esempio, invio automatico di un file alla chat
        try:
            folder_report = daily_routine_command()
            # Ottieni il percorso completo della cartella
            folder_path = os.path.join(os.getcwd(), folder_report)

            # Verifica che la cartella esista
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Ottieni la lista dei file nella cartella
                files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

                # Invia ciascun file alla chat
                for chat_id in self.lista_chat_id:  # Sostituisci con l'ID effettivo della tua chat
                    for file_name in files:
                        file_path = os.path.join(folder_path, file_name)
                        self.send_generated_pdf(self.bot, chat_id, file_path)

                    print(f"Tutti i file sono stati inviati alle chat.")
            else:
                print(f"La cartella non esiste: {folder_path}")

        except Exception as e:
            self.logger.error(f"Errore durante l'esecuzione della routine giornaliera: {e}")

    def weekly_routine(self):
        # Logica della tua routine quotidiana qui
        # Ad esempio, invio automatico di un file alla chat
        try:
            folder_report = weekly_routine_command()
            # Ottieni il percorso completo della cartella
            folder_path = os.path.join(os.getcwd(), folder_report)

            # Verifica che la cartella esista
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Ottieni la lista dei file nella cartella
                files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

                # Invia ciascun file alla chat
                for chat_id in self.lista_chat_id:  # Sostituisci con l'ID effettivo della tua chat
                    for file_name in files:
                        file_path = os.path.join(folder_path, file_name)
                        self.send_generated_pdf(self.bot, chat_id, file_path)

                    print(f"Tutti i file sono stati inviati alle chat.")
            else:
                print(f"La cartella non esiste: {folder_path}")

        except Exception as e:
            self.logger.error(f"Errore durante l'esecuzione della routine giornaliera: {e}")

    def create_level_menu(self, menu="top"):
        # Creazione dei bottoni per il menu principale
        if menu == 'specialtool':
            keyboard = [
                [InlineKeyboardButton("TBD1", callback_data="action_buildsuppres"),
                 InlineKeyboardButton("TBD2", callback_data="action_option2")],
                [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]
            ]
        elif menu == 'crypto':
            keyboard = [
                [InlineKeyboardButton("TBD", callback_data="action_updatedaily"),
                 InlineKeyboardButton("TBD", callback_data="action_updateweekly")],
                [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]
            ]
        elif menu == 'catchtrade':
            keyboard = [
                [InlineKeyboardButton("S&P500", callback_data="menu_catchtradesp500"),
                 InlineKeyboardButton("Nasdaq100", callback_data="menu_catchtradenasdaq")],
                [InlineKeyboardButton("Russel2000", callback_data="menu_catchtraderussel"),
                 InlineKeyboardButton("method 4", callback_data="menu_option_4")],
                [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]
            ]
        elif menu == 'macrotool':
            keyboard = [
                [InlineKeyboardButton("Update data", callback_data="action_updatemacrodata"),
                 InlineKeyboardButton("Download report", callback_data="action_downloadmacroreport")],
                [InlineKeyboardButton("Back to main menu", callback_data="menu_top")]
            ]
        elif menu == 'top':
            keyboard = [
                [InlineKeyboardButton("Stock", callback_data="menu_catchtrade"),
                 InlineKeyboardButton("Cripto", callback_data="menu_crypto")],
                [InlineKeyboardButton("Macroeconomic tool", callback_data="menu_macrotool"),
                 InlineKeyboardButton("Special Tool", callback_data="menu_specialtool")]
            ]
        elif menu == 'catchtraderussel':
            keyboard = [
                [InlineKeyboardButton("find blocked stock", callback_data="action_findblockedstockrussel"),
                 InlineKeyboardButton("catch possible breakout", callback_data="action_findbreakoutrussel")],
                [InlineKeyboardButton("catch possible fakeout", callback_data="action_findfakeoutrussel"),
                 InlineKeyboardButton("TBD", callback_data="action_findlateralmovsp500")],
                [InlineKeyboardButton("Back to previous menu", callback_data="menu_catchtrade")]
            ]
        elif menu == 'catchtradesp500':
            keyboard = [
                [InlineKeyboardButton("find blocked stock", callback_data="action_findblockedstocksp500"),
                 InlineKeyboardButton("catch possible breakout", callback_data="action_findlbreakoutsp500")],
                [InlineKeyboardButton("catch possible fakeout", callback_data="action_findfakeoutsp500"),
                 InlineKeyboardButton("TBD", callback_data="action_findlateralmovsp500")],
                [InlineKeyboardButton("Back to previous menu", callback_data="menu_catchtrade")]
            ]
        elif menu == 'catchtradenasdaq':
            keyboard = [
                [InlineKeyboardButton("find blocked stock", callback_data="action_findblockedstocknasdaq"),
                 InlineKeyboardButton("catch possible breakout", callback_data="action_findbreakoutnasdaq")],
                [InlineKeyboardButton("catch possible fakeout", callback_data="action_findfakeoutnasdaq"),
                 InlineKeyboardButton("TBD", callback_data="action_findlateralmovsp500")],
                [InlineKeyboardButton("Back to previous menu", callback_data="menu_catchtrade")]
            ]
        else:
            keyboard = self.create_level_menu('top')

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
        elif action == "findblockedstockrussel":
            try:
                file_report = blocked_stock(index="Russel")
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")
        elif action == "findblockedstocksp500":
            try:
                file_report = blocked_stock(index="SP500")
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")
        elif action == "findblockedstocknasdaq":
            try:
                file_report = blocked_stock(index="Nasdaq")
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")
        elif action == "findbreakoutrussel":
            try:
                file_report = breakout_finder(index="Russel")
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")
        elif action == "findlbreakoutsp500":
            try:
                file_report = breakout_finder(index="SP500")
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")
        elif action == "findbreakoutnasdaq":
            try:
                file_report = breakout_finder(index="Nasdaq")
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")
        elif action == "findfakeoutrussel":
            try:
                file_report = fakeout_finder(index="Russel")
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")
        elif action == "findfakeoutsp500":
            try:
                file_report = fakeout_finder(index="SP500")
                self.send_generated_pdf(client, callback_query.message.chat.id, file_report)
                callback_query.message.reply_text("PDF generate and sent!")
            except subprocess.CalledProcessError as e:
                callback_query.message.reply_text(f"Error generate: {e}")
        elif action == "findfakeoutnasdaq":
            try:
                file_report = fakeout_finder(index="Nasdaq")
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