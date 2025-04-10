import logging
import os
import inspect
from datetime import datetime

class Logger:
    def __init__(self, log_file: str):
        self.log_file = log_file

        # Creazione della directory se non esiste
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Creazione del logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # Mantiene tutti i log nel file

        # Rimuove eventuali handler pre-esistenti (evita duplicati)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Handler per scrivere nel file (sovrascrive a ogni avvio)
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)

        # Handler per stampare a schermo solo i log di livello INFO o superiori
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(console_formatter)

        # Aggiunta degli handler al logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log(self, message: str, stock: str = "N/A", level: str = "info"):
        """Logga un messaggio con data, ora, funzione chiamante e stock."""
        caller_function = inspect.stack()[1].function  # Ottiene il nome della funzione chiamante
        log_message = f"[{caller_function}] [{stock}] {message}"

        # Log in base al livello
        if level.lower() == "debug":
            self.logger.debug(log_message)
        elif level.lower() == "warning":
            self.logger.warning(log_message)
        elif level.lower() == "error":
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)  # Stampato a schermo e scritto nel file

class LoggerSingleton:
    _instance = None

    @classmethod
    def get_logger(cls, log_file=None):
        if cls._instance is None:
            if log_file is None:
                raise ValueError("You must provide a log file path for first initialization")
            cls._instance = Logger(log_file)
        return cls._instance


# Esempio di utilizzo
if __name__ == "__main__":
    log = Logger("logs/trading_log.txt")

    def example_function():
        stock = "AAPL"
        log.log("Entrando in posizione", stock, level="info")
        log.log("Attenzione: volatilità alta", stock, level="warning")
        log.log("Errore: connessione persa", stock, level="error")

    example_function()
