from Reports.report_builder import ReportGenerator
import json
import pandas as pd
from libs.filtered_stock import return_filtred_list
import time
from libs.detectors.support_resistence_handler import SupportResistanceFinder
from Trading.methodology.SuppRes.SR_construction import StockAnalysis


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

                if result:
                    report.add_content(f'stock = {item} \n')
                    report.add_content(f'S/R= {result} \n')


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
