from Reports.image_builder import CandlestickChartGenerator
from Trading.methodology.blocked_stock.blocked_stock import TradingAnalyzer
from Trading.methodology.lateral_movement.search_type_mov import TrendMovementAnalyzer
from TelegramBot.commander.download_data import *
from support.miscela import *
# from Trading.methodology.Asaf_method.Asaf_strategy import Asaf_trading
from Trading.methodology.Asaf_method.Optim_Asaf_strategy import *

# from Trading.methodology.PriceAction.build_json_convergence import create_file_report


source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
def download_data(interval='1d'):
    with open(f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)

    # Lista dei ticker
    tickers_list = list(tickers.keys())

    # Utilizzo della classe StockDataDownloader con l'intervallo specificato
    downloader = StockDataDownloader(tickers_list, interval=interval)
    # downloader.download_data()

def blocked_stock(index="Russel"):
    #start_time = time.time()
    report = ReportGenerator()
    report.add_title(title=f"{index} Report blocked stock")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    tickers_list = return_filtred_list(index=index)
    # Controlla se la lista dei ticker è vuota
    if not tickers_list:
        # Aggiungi un messaggio nel report o registra un log
        report.add_content("Nessun ticker soddisfa i criteri di selezione.")
        print("Nessun ticker soddisfa i criteri di selezione.")
    else:

        for item in tickers_list:
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv",
                                   parse_dates=['Date'])
                data = data.tail(60)
                enhanced_strategy = TradingAnalyzer(data)
                print(f'stock = {item}')
                result, image, new_data = enhanced_strategy.check_signal(period=20)
                if result:
                    report.add_content(f'stock = {item} \n')
                    report.add_commented_image(df=data, comment=f'Description = {result["details"]}', image_path=image)

                last_signal = new_data['signal'].iloc[-1]
                if last_signal == 1:
                    print(f"Segnale di vendita (sell) per {item}")
                    # Aggiungi logica per gestire il segnale di vendita
                elif last_signal == 2:
                    print(f"Segnale di acquisto (buy) per {item}")
                    # Aggiungi logica per gestire il segnale di acquisto
            except FileNotFoundError:
                    # Gestisci l'errore se il file non viene trovato
                    print(f"File non trovato per {item}")
            except Exception as e:
                # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")
        # Salva il report e pulisci i file temporanei
        file_report = report.save_report(filename=f"{index}_Report_blocked_stock")
        enhanced_strategy.clear_img_temp_files()
        #end_time = time.time()  # Registra l'ora di fine
        #duration = end_time - start_time  # Calcola la durata totale
        #print(f"Tempo di elaborazione {index}: {duration} secondi.")
        return file_report


def find_lateral_mov():
    report = ReportGenerator()
    report.add_title(title="Report lateral movement")

    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    with open(f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
        tickers = json.load(file)
        tickers_list = list(tickers.keys())

    for item in tickers_list:
        data = pd.read_csv(f"{source_directory}/Data/Daily/{item}_historical_data.csv")
        if data["Close"].iloc[-1] < 50:
            enhanced_strategy = TrendMovementAnalyzer(data)
            image = CandlestickChartGenerator(data)
            result = enhanced_strategy.evaluate_trend_and_laterality( lateral_check_method="ADX")
            if result:
                image = image.create_simple_chart(max_points=50)
                print(f'stock = {item} -- FOUND ')
                report.add_content(f'stock = {item} ')
                report.add_commented_image(df=data, comment=f'Description', image_path=image)
            print(f"checked stock {item}")
        else:
            print(f"stock {item} is over price")
    file_report = report.save_report(filename="Report_lateral_movement")
    enhanced_strategy.clear_img_temp_files()
    return file_report

# def daily_routine_command():
#     download_data(interval="5m")
#     download_data()
#     file_report1 = blocked_stock(index="SP500")
#     file_report2 = blocked_stock(index="Nasdaq")
#     file_report3 = Asaf_trading(index="SP500")
#     # file_report4 = create_file_report(index="SP500")
#     # file_report5 = create_file_report(index="Nasdaq")
#     file_report6 = Asaf_trading(index="Nasdaq")
#     folder_name = crea_cartella_con_data()
#     sposta_file_in_cartella(file_report1, folder_name)
#     sposta_file_in_cartella(file_report2, folder_name)
#     sposta_file_in_cartella(file_report3, folder_name)
#     # sposta_file_in_cartella(file_report4, folder_name)
#     # sposta_file_in_cartella(file_report5, folder_name)
#     sposta_file_in_cartella(file_report6, folder_name)
#     return folder_name
#
#
# def weekly_routine_command():
#     download_data(interval="1wk")
#     folder_name = crea_cartella_con_data()
#     file_report1 = ema_cross_trading(index="SP500")
#     file_report2 = ema_cross_trading(index="Nasdaq")
#     file_report3 = sma_cross_trading(index="SP500")
#     file_report4 = sma_cross_trading(index="Nasdaq")
#     file_report5 = sma_cross_trading(index="Russel")
#     file_report6 = ema_cross_trading(index="Russel")
#
#     sposta_file_in_cartella(file_report1, folder_name)
#     sposta_file_in_cartella(file_report2, folder_name)
#     sposta_file_in_cartella(file_report3, folder_name)
#     sposta_file_in_cartella(file_report4, folder_name)
#     sposta_file_in_cartella(file_report5, folder_name)
#     sposta_file_in_cartella(file_report6, folder_name)
#
#     return folder_name


# def generate_and_move_reports(indices, strategies_BT, folder_name):
#     for index in indices:
#         for strategy in strategies_BT:
#             file_report = strategy(index=index)
#             sposta_file_in_cartella(file_report, folder_name)
#
# def routine_command(interval_type, indices):
#     if interval_type == "daily":
#         download_data(interval="5m")
#         download_data()
#         strategies_BT = [blocked_stock, Asaf_trading]
#     elif interval_type == "weekly":
#         download_data(interval="1wk")
#         strategies_BT = [ema_cross_trading, sma_cross_trading]
#     else:
#         raise ValueError("Invalid interval type. Use 'daily' or 'weekly'.")
#
#     folder_name = crea_cartella_con_data()
#     generate_and_move_reports(indices, strategies_BT, folder_name)
#     return folder_name
#
#
# def routine( interval_type):
#     # Logica della routine
#     try:
#         folder_report = bot_command.routine_command(interval_type=interval_type,
#                                                     indices=["SP500", "Nasdaq", "Russel"])
#         folder_path = os.path.join(os.getcwd(), folder_report)
#
#         # Verifica che la cartella esista
#         if os.path.exists(folder_path) and os.path.isdir(folder_path):
#             # Ottieni la lista dei file nella cartella
#             files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
#
#             # Invia ciascun file alla chat
#             for chat_id in self.lista_chat_id:
#                 for file_name in files:
#                     file_path = os.path.join(folder_path, file_name)
#                     self.send_generated_pdf(self.bot, chat_id, file_path)
#
#                 print(f"Tutti i file sono stati inviati alle chat.")
#         else:
#             print(f"La cartella non esiste: {folder_path}")
#
#     except Exception as e:
#         self.logger.log(f"Errore durante l'esecuzione della routine {interval_type}: {e}")

if __name__ == '__main__':
    pass