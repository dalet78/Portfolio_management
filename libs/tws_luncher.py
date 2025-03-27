import subprocess
import psutil
import time
import logging
import os


def is_tws_running():
    """Verifica se TWS è già in esecuzione."""
    for process in psutil.process_iter(attrs=["name"]):
        if "tws" in process.info["name"].lower():
            return True
    return False


class TWSLauncher:
    """Gestisce l'avvio e l'autenticazione di Trader Workstation (TWS)."""

    def __init__(self, tws_path, username, password):
        self.tws_path = tws_path
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def start_tws(self):
        """Avvia TWS se non è già in esecuzione."""
        if is_tws_running():
            self.logger.info("TWS è già in esecuzione.")
            return

        try:
            self.logger.info("Avvio di TWS...")
            subprocess.Popen([self.tws_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(10)  # Attendi qualche secondo per assicurarti che TWS sia avviato
            self.logger.info("TWS avviato con successo!")
            self.login()
        except Exception as e:
            self.logger.error(f"Errore nell'avvio di TWS: {e}")

    def login(self):
        """Esegue automaticamente il login in TWS."""
        try:
            import pyautogui
            self.logger.info("Attesa della finestra di login...")
            time.sleep(5)  # Tempo per caricare la finestra di login

            pyautogui.write(self.username)
            pyautogui.press('tab')
            pyautogui.write(self.password)
            pyautogui.press('enter')
            self.logger.info("Login effettuato con successo!")
        except Exception as e:
            self.logger.error(f"Errore durante il login: {e}")

    def stop_tws(self):
        """Chiude TWS se è in esecuzione."""
        for process in psutil.process_iter(attrs=["pid", "name"]):
            if "tws" in process.info["name"].lower():
                self.logger.info(f"Chiudo TWS (PID: {process.info['pid']})...")
                psutil.Process(process.info["pid"]).terminate()
                break
        else:
            self.logger.info("TWS non è in esecuzione.")


# Esempio di utilizzo
if __name__ == "__main__":
    tws_path = os.path.expanduser("~/Jts/tws")
    # Modifica il percorso in base al tuo sistema operativo
    username = "hcuckr695"
    password = "IlanaQ!W@e3r4t5"

    tws = TWSLauncher(tws_path, username, password)
    tws.start_tws()
