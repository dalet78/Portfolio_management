import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
import pandas as pd
import time
from libs.indicators.vwap_handler import  TradingVWAP
from libs.filtered_stock import return_filtred_list
from market_profile import MarketProfile



def vmp_stock_finder(index="Russel"):
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
                # results_df = pd.DataFrame(columns=['Date', 'POC', 'HVN', 'LVN'])
                data = pd.read_csv(f"{source_directory}/Data/{index}/5min/{item}_historical_data.csv",
                                   parse_dates=['Datetime'])
                # Sostituisci con il percorso del tuo file
                  # Ensure this has 'Datetime', 'Price', and 'Volume'
                if not {'Datetime', 'High', 'Low', 'Open', 'Close', 'Volume'}.issubset(data.columns):
                    raise ValueError("Il DataFrame deve contenere le colonne 'Date', 'High', 'Low', 'Open', 'Close' e 'Volume'.")

                data.set_index('Datetime', inplace=True)
                # Inizializza un DataFrame per i risultati
                results_df = pd.DataFrame(columns=['Date', 'ValueAreaHigh', 'Poc', 'ValueAreaLow'])

                for date, daily_data in data.groupby(data.index.date):
                    # Create a MarketProfile object for that day's data
                    mp = MarketProfile(daily_data)
                    mp_slice = mp[daily_data.index.min():daily_data.index.max()]

                    # Calculate the market profile for the day
                    # mp_slice.make()  # Uncomment this line if 'make' method exists and is required

                    # Extract the value area high and low
                    va_high = mp_slice.value_area[1]
                    va_low = mp_slice.value_area[0]
                    poc = mp_slice.poc_price

                    # Create a new row with the calculated data
                    new_row = pd.DataFrame({
                        'Date': [date],
                        'ValueAreaHigh': [va_high],
                        'Poc': [poc],
                        'ValueAreaLow': [va_low]
                    })

                    # Append the new row to the results DataFrame
                    results_df = pd.concat([results_df, new_row], ignore_index=True)

                # Salva i risultati in un file CSV
                results_df.to_csv(f'{source_directory}/Data/VMP/{item}_value_area_daily.csv', index=False)

            except FileNotFoundError:
                print(f"File non trovato per {item}")
            except Exception as e:
                print(f"Errore durante l'elaborazione di {item}: {e}")

            file_report = report.save_report(filename=f"{index}_vwap_analysis")
            print(f"Report salvato in: {file_report}")
            duration = time.time() - start_time
            print(f"Tempo di esecuzione: {duration:.2f} secondi")

if __name__ == '__main__':
    vmp_stock_finder(index="Nasdaq")
    vmp_stock_finder(index="SP500")