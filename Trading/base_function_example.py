from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
import pandas as pd
import time
from libs.indicators.vwap_handler import  TradingVWAP
from libs.filtered_stock import return_filtred_list
from market_profile import MarketProfile
import pandas_datareader as data
import os

def daily_rsi_detector(index="SP500"):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Possible vwap stock")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    tickers_list = return_filtred_list(index=index)
    close_to_vwap_stocks = []
    # Controlla se la lista dei ticker è vuota
    if not tickers_list:
        # Aggiungi un messaggio nel report o registra un log
        report.add_content("Nessun ticker soddisfa i criteri di selezione.")
        print("Nessun ticker soddisfa i criteri di selezione.")
    else:

        for item in tickers_list:
            print(f'Analyze stock = {item}')
            result = False
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/5min/{item}_historical_data.csv",
                                   parse_dates=['Datetime'])

                if not {'Datetime', 'High', 'Low', 'Open', 'Close', 'Volume'}.issubset(data.columns):
                    raise ValueError(
                        "Il DataFrame deve contenere le colonne 'Date', 'High', 'Low', 'Open', 'Close' e 'Volume'.")
##############################################################################################
################################ Insert code here ############################################
##############################################################################################




##############################################################################################
            except FileNotFoundError:
                print(f"File non trovato per {item}")
            except Exception as e:
                print(f"Errore durante l'elaborazione di {item}: {e}")

####### Change name of report #################################################################
        file_report = report.save_report(filename=f"{index}_vwap_analysis")
        print(f"Report salvato in: {file_report}")
        duration = time.time() - start_time
        print(f"Tempo di esecuzione: {duration:.2f} secondi")



if __name__ == '__main__':
    daily_rsi_detector(index = "Nasdaq")
    daily_rsi_detector(index = "SP500")
    #vwap_stock_finder(index="Russel")