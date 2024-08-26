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

# Funzione per calcolare l'RSI
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def return_high_session(data, indice):
    return data.loc[indice, "High"]

def return_low_session(data, indice):
    return data.loc[indice, "Low"]
# Funzione per verificare se il primo massimo ha un RSI sopra 70 o sotto i 30
def check_peak_rsi(rsi):
    if rsi > 70:
        return "Il picco ha un RSI sopra 70."
    elif rsi < 30:
        return "Il picco ha un RSI sotto 30."
    else:
        return "Il picco non soddisfa i criteri di RSI."

# Funzione per confrontare i valori RSI dei due picchi
def compare_peak_rsi(first_peak_rsi, second_peak_rsi):
    if first_peak_rsi > 70:
        if second_peak_rsi < first_peak_rsi:
            return "Il secondo picco ha un RSI inferiore al primo picco."
        else:
            return "Il secondo picco ha un RSI superiore o uguale al primo picco."
    elif first_peak_rsi < 30:
        if second_peak_rsi > first_peak_rsi:
            return "Il secondo picco ha un RSI superiore al primo picco."
        else:
            return "Il secondo picco ha un RSI inferiore o uguale al primo picco."
    else:
        return "Il primo picco non soddisfa i criteri di RSI."

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
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv",
                                   parse_dates=['Date'])

                if not {'Date', 'High', 'Low', 'Open', 'Close', 'Volume'}.issubset(data.columns):
                    raise ValueError(
                        "Il DataFrame deve contenere le colonne 'Date', 'High', 'Low', 'Open', 'Close' e 'Volume'.")
##############################################################################################
################################ Insert code here ############################################
##############################################################################################
                    # Calcola l'RSI
                data['RSI'] = calculate_rsi(data['Close'])

                # Trova i due massimi o minimi
                max_values = data['Close'].rolling(window=10, min_periods=1).apply(lambda x: x.argmax(), raw=True)
                min_values = data['Close'].rolling(window=10, min_periods=1).apply(lambda x: x.argmin(), raw=True)

                max_values = max_values[max_values.diff() > 1]
                min_values = min_values[min_values.diff() > 1]

                # print("Massimi:", data.loc[max_values])
                # print("Minimi:", data.loc[min_values])

                if len(max_values) >= 2:
                    last_2_index= max_values.tail(2).index
                    first_peak_index = last_2_index[0]
                    second_peak_index = last_2_index[-1]
                    first_peak_rsi = data.loc[first_peak_index, 'RSI']
                    second_peak_rsi = data.loc[second_peak_index, 'RSI']
                    first_peak_high = return_high_session(data, first_peak_index)
                    second_peak_high = return_high_session(data, second_peak_index)

                    if first_peak_rsi >70 and second_peak_rsi< first_peak_rsi and second_peak_high > first_peak_high:
                        report.add_content(f"stock = {item}")
                        report.add_content(f"RSI div found overbuy")
                        report.add_content((f"First RSI {first_peak_rsi.round(2)} - Date {data.loc[first_peak_index, 'Date']} "
                                            f"price High {first_peak_high}"))
                        report.add_content(
                            (f"First RSI {second_peak_rsi.round(2)} - Date {data.loc[second_peak_index, 'Date']} "
                             f"price High {second_peak_high.round(2)}"))
                    # print(f"Primo picco - RSI: {first_peak_rsi}, Secondo picco - RSI: {second_peak_rsi}")
                    #
                    # print("Primo picco:", check_peak_rsi(first_peak_rsi))
                    # print("Secondo picco:", check_peak_rsi(second_peak_rsi))
                    # print("Confronto tra i picchi:", compare_peak_rsi(first_peak_rsi, second_peak_rsi))

                if len(min_values) >= 2:
                    last_2_index = min_values.tail(2).index
                    first_peak_index = last_2_index[0]
                    second_peak_index = last_2_index[-1]
                    first_peak_rsi = data.loc[first_peak_index, 'RSI']
                    second_peak_rsi = data.loc[second_peak_index, 'RSI']
                    first_peak_low = return_low_session(data, first_peak_index)
                    second_peak_low = return_low_session(data, second_peak_index)

                    if first_peak_rsi < 30 and second_peak_rsi > first_peak_rsi and first_peak_low > second_peak_low:
                        report.add_content(f"stock = {item}")
                        report.add_content(f"RSI div found oversell")
                        report.add_content(
                            (f"First RSI {first_peak_rsi.round(2)} - Date {data.loc[first_peak_index, 'Date']} "
                             f"price High {first_peak_low}"))
                        report.add_content(
                            (f"First RSI {second_peak_rsi.round(2)} - Date {data.loc[second_peak_index, 'Date']} "
                             f"price High {second_peak_low.round(2)}"))
                    # print(f"Primo picco - RSI: {first_peak_rsi}, Secondo picco - RSI: {second_peak_rsi}")
                    #
                    # print("Primo picco:", check_peak_rsi(first_peak_rsi))
                    # print("Secondo picco:", check_peak_rsi(second_peak_rsi))
                    # print("Confronto tra i picchi:", compare_peak_rsi(first_peak_rsi, second_peak_rsi))

##############################################################################################
            except FileNotFoundError:
                print(f"File non trovato per {item}")
            except Exception as e:
                print(f"Errore durante l'elaborazione di {item}: {e}")

####### Change name of report #################################################################
        file_report = report.save_report(filename=f"{index}_rsi_detector")
        print(f"Report salvato in: {file_report}")
        duration = time.time() - start_time
        print(f"Tempo di esecuzione: {duration:.2f} secondi")



if __name__ == '__main__':
    daily_rsi_detector(index = "Nasdaq")
    daily_rsi_detector(index = "SP500")
    #vwap_stock_finder(index="Russel")