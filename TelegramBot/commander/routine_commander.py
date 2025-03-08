from support.miscela import *
from configuration import methodology_configuration
import importlib





def routine(bot_instance, interval_type):
    """Esegue la routine per generare e inviare i report."""
    report_files= strategies_routine(bot_instance, interval_type)
    report_files= opportunites_routine(bot_instance, interval_type)
    send_reports_to_chats(bot_instance, report_files)

def strategies_routine(bot_instance, interval_type):
    try:
        strategies = get_strategies(interval_type)
        folder_report = generate_reports(strategies, indices=["ALL"])
        return get_report_files(folder_report)

    except Exception as e:
        print(f"Errore durante l'esecuzione della strategies routine {interval_type}: {e}")


    except Exception as e:
        print(f"Errore durante l'esecuzione della strategies routine {interval_type}: {e}")

def opportunites_routine(bot_instance,interval_type):
    try:
        opportunites = get_opportunites(interval_type)
        # Genera il report e ottiene la cartella
        folder_report = generate_reports(opportunites, indices=["ALL"])

        # Ottiene la lista di file dalla cartella
        return get_report_files(folder_report)

        # Invia i file alle chat
        # send_reports_to_chats(bot_instance, report_files)

    except Exception as e:
        print(f"Errore durante l'esecuzione della opportunities routine {interval_type}: {e}")

def generate_reports(strategies, indices):
    """Genera i report basandosi sui dati scaricati e sulle strategie selezionate."""

    folder_name = crea_cartella_con_data()
    generate_and_move_reports(indices, strategies, folder_name)
    return folder_name

# def routine_command(interval_type, indices):
#     if interval_type == "daily":
#         download_data(interval="5m")
#         download_data()
#         strategies_BT = [Asaf_trading]
#     elif interval_type == "weekly":
#         download_data(interval="1wk")
#         strategies_BT = [ema_cross_trading, sma_cross_trading]
#     else:
#         raise ValueError("Invalid interval type. Use 'daily' or 'weekly'.")
#
#     folder_name = crea_cartella_con_data()
#     generate_and_move_reports(indices, strategies_BT, folder_name)
#     return folder_name

def generate_and_move_reports(indices, strategies, folder_name):
    for index in indices:
        for module_name, function_name in strategies:
            # Importa dinamicamente il modulo
            module = importlib.import_module(module_name)

            # Ottieni la funzione dal modulo
            strategy_function = getattr(module, function_name)

            # Esegui la funzione e ottieni il report
            file_report = strategy_function(index=index)

            # Sposta il file nella cartella desiderata
            sposta_file_in_cartella(file_report, folder_name)

def get_report_files( folder_name):
    """Restituisce la lista completa di file PDF nella cartella specificata."""
    folder_path = os.path.join(os.getcwd(), folder_name)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"La cartella {folder_path} non esiste!")
        return []

    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return files

def send_reports_to_chats(bot_instance, file_paths):
    """Invia i report a tutte le chat Telegram registrate."""
    if not file_paths:
        print("Nessun file da inviare.")
        return

    for chat_id in bot_instance.lista_chat_id:
        for file_path in file_paths:
            bot_instance.send_generated_pdf(bot_instance.bot, chat_id, file_path)

    bot_instance.logger.info("Tutti i file sono stati inviati con successo.")


def get_strategies(interval_type):
    """Restituisce la lista di strategie in base al tipo di intervallo specificato."""

    """
        Restituisce la lista di strategie per l'intervallo specificato.

        :param interval: L'intervallo di riferimento (ad esempio "5m", "daily", "weekly")
        :return: Lista di strategie per l'intervallo fornito, oppure una lista vuota se l'intervallo non è valido
        """
    return methodology_configuration.INTERVAL_STRATEGIES.get(interval_type, [])

def get_opportunites(interval_type):
    """Restituisce la lista di strategie in base al tipo di intervallo specificato."""

    """
        Restituisce la lista di strategie per l'intervallo specificato.

        :param interval: L'intervallo di riferimento (ad esempio "5m", "daily", "weekly")
        :return: Lista di strategie per l'intervallo fornito, oppure una lista vuota se l'intervallo non è valido
        """
    return methodology_configuration.INTERVAL_OPPORTUNITES.get(interval_type, [])


if __name__ == '__main__':
    routine(interval_type="5m")