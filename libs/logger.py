import logging
from datetime import datetime
import os

class MyLogger:
    """
    Utilizzo della classe
    from libs.logger import MyLogger
    
    logger = MyLogger("my_log_file.log")
    logger.info("Questo è un messaggio informativo.")
    logger.warning("Questo è un messaggio di avviso.")
    logger.error("Questo è un messaggio di errore.")
    logger.create_report()
    """
    def __init__(self, log_file_name):
        self.log_file_name = log_file_name
        logging.basicConfig(filename=self.log_file_name, level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def info(self, message):
        logging.info(message)

    def warning(self, message):
        logging.warning(message)

    def error(self, message):
        logging.error(message)

    def create_report(self):
        # Aggiunge una riga al file di report ogni volta che il programma viene eseguito
        with open("report.txt", "a") as report_file:
            report_file.write(f"Programma eseguito il {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_file.write(f"Log salvato in: {self.log_file_name}\n")

