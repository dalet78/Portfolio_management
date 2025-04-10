import subprocess
import psutil
import time
import os
from support.logger import LoggerSingleton


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
        self.logger = LoggerSingleton.get_logger()  # ✅ logger unificato

    def start_tws(self):
        """Avvia TWS se non è già in esecuzione."""
        if is_tws_running():
            self.logger.log("TWS è già in esecuzione.", level="info")
            return

        try:
            self.logger.log("Avvio di TWS...", level="info")
            subprocess.Popen([self.tws_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(10)  # Attendi qualche secondo per assicurarti che TWS sia avviato
            self.logger.log("TWS avviato con successo!", level="info")
            self.login()
        except Exception as e:
            self.logger.log(f"Errore nell'avvio di TWS: {e}", level="error", exc_info=True)

    def login(self):
        try:
            import pyautogui
            self.logger.log("Attesa della finestra di login...", level="info")
            time.sleep(5)

            pyautogui.write(self.username)
            pyautogui.press('tab')
            pyautogui.write(self.password)
            pyautogui.press('enter')
            time.sleep(10)  # <-- aumenta la pausa dopo login

            self.logger.log("Login effettuato con successo!", level="info")
        except Exception as e:
            self.logger.log(f"Errore durante il login: {e}", level="error", exc_info=True)

    def stop_tws(self):
        """Chiude TWS se è in esecuzione."""
        for process in psutil.process_iter(attrs=["pid", "name"]):
            if "tws" in process.info["name"].lower():
                self.logger.log(f"Chiudo TWS (PID: {process.info['pid']})...", level="info")
                psutil.Process(process.info["pid"]).terminate()
                break
        else:
            self.logger.log("TWS non è in esecuzione.", level="info")

    def wait_until_tws_ready(self, timeout=120, interval=5):
        """Attende finché TWS è pronto ad accettare connessioni tramite ib_insync."""
        from ib_insync import IB
        self.logger.log("⌛ Verifico connessione API TWS tramite ib_insync...", level="info")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                ib = IB()
                ib.connect("127.0.0.1", 7497, clientId=999, timeout=10)
                self.logger.log("✅ Connessione API a TWS riuscita!", level="info")
                ib.disconnect()
                return True
            except Exception as e:
                self.logger.log(f"⏳ TWS non ancora pronto: {type(e).__name__}: {e}", level="debug")
                time.sleep(interval)

        self.logger.log("❌ Timeout: la connessione API a TWS non è riuscita", level="error")
        return False


# Esempio di utilizzo
if __name__ == "__main__":
    tws_path = os.path.expanduser("~/Jts/tws")  # Modifica se necessario
    username = "hcuckr695"
    password = "IlanaQ!W@e3r4t5"

    tws = TWSLauncher(tws_path, username, password)
    tws.start_tws()
