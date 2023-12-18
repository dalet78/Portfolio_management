from Reports.report_builder import ReportGenerator
import json
import pandas as pd
from libs.filtered_stock import return_filtred_list
import time
from libs.detectors.support_resistence_handler import SupportResistanceFinder
from Trading.methodology.SuppRes.SR_construction import StockAnalysis

import numpy as np
import yfinance as yf
from sklearn.cluster import KMeans


# class SupportResistanceFinder:
#     def __init__(self, data, n_clusters=7, radius=0.5):
#         self.n_clusters = n_clusters
#         self.radius = radius
#         self.data = data
#
#     def identify_pivots(self, close_prices, thresholds=(25, 50, 75), days=(5, 5, 3)):
#         pivots = []
#         for i in range(max(days), len(close_prices) - max(days)):
#             # Determinare il numero di giorni da considerare in base al prezzo
#             if close_prices.iloc[i] < thresholds[0]:
#                 day_range = days[0]
#             elif close_prices.iloc[i] < thresholds[1]:
#                 day_range = days[1]
#             elif close_prices.iloc[i] < thresholds[2]:
#                 day_range = days[2]
#             else:
#                 day_range = days[-1]  # Usa 3 giorni per prezzi superiori a 75
#
#             max_range = close_prices[i - day_range:i + day_range + 1]
#             min_range = close_prices[i - day_range:i + day_range + 1]
#
#             if close_prices.iloc[i] == max_range.max():
#                 pivots.append(close_prices.iloc[i])
#             elif close_prices.iloc[i] == min_range.min():
#                 pivots.append(close_prices.iloc[i])
#
#         return pivots
#
#     def find_levels(self):
#         close_prices = self.data['Close']
#         pivot_points = self.identify_pivots(close_prices)
#
#         # Se non ci sono abbastanza punti di pivot, ritorna un messaggio di errore
#         if len(pivot_points) < self.n_clusters:
#             return "Non ci sono abbastanza punti di pivot per applicare K-means"
#
#         # Applicazione del K-means ai punti di pivot
#         kmeans = KMeans(n_clusters=self.n_clusters)
#         kmeans.fit(np.array(pivot_points).reshape(-1, 1))
#         levels = kmeans.cluster_centers_
#
#         return np.sort(levels.round(2), axis=0), self.data



def main(index="SP500"):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
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
                # data = data.tail(180)
                enhanced_strategy = SupportResistanceFinder(data)
                print(f'stock = {item}')
                result, new_data = enhanced_strategy.find_levels(dynamic_cluster= False)
                # filtred_interesting_dataset =new_data[new_data['is_interesting'] != 0]
                # count_interesting = filtred_interesting_dataset['is_interesting'].count()
                # filtred_signal_dataset = new_data[new_data['signal'] != 0]
                # count_signal = filtred_signal_dataset['signal'].count()
                if result:
                    report.add_content(f'stock = {item} \n')
                    report.add_content(f'S/R= {result} \n')
                    #report.add_commented_image(df=data, comment=f'Description = {result["details"]}', image_path=image)
                # if not filtred_interesting_dataset.empty:
                #     report.add_content(f'stock = {item} \n count interesting= {count_interesting}\n')
                #     report.add_content(f'stock = {item} \n count signal= {count_signal}\n')
                #last_signal = new_data['signal'].iloc[-1]
                #if last_signal == 1:
                 #   print(f"Segnale di vendita (sell) per {item}")
                    # Aggiungi logica per gestire il segnale di vendita
                #elif last_signal == 2:
                 #   print(f"Segnale di acquisto (buy) per {item}")
                    # Aggiungi logica per gestire il segnale di acquisto

            except FileNotFoundError:
                # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
                # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")

        # Salva il report e pulisci i file temporanei
    file_report = report.save_report(filename=f"{index}_Report_blocked_stock")
    #enhanced_strategy.clear_img_temp_files()
    end_time = time.time()  # Registra l'ora di fine
    duration = end_time - start_time  # Calcola la durata totale

    print(f"Tempo di elaborazione {index}: {duration} secondi.")

    return file_report


if __name__ == '__main__':
    file_report = main()
    print(file_report)
