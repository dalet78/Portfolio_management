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



def calculate_overlap(interval1, interval2):
    start1, end1 = interval1
    start2, end2 = interval2
    overlap = max(0, min(end1, end2) - max(start1, start2))
    return overlap


def df_last_5_days(df):
    df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True)

    # Ordina il DataFrame in base alla colonna "Datetime"
    df = df.sort_values(by='Datetime')

    # Dividi il DataFrame in singole giornate
    days = [g for _, g in df.groupby(df['Datetime'].dt.date)]

    # Seleziona solo gli ultimi cinque giorni
    last_5_days = days[-5:]

    # Costruisci i 5 DataFrame con gli ultimi cinque giorni
    # df_last_5_days = [pd.concat(g, ignore_index=True) for g in [last_5_days]]
    return last_5_days

def return_market_profile(array_df):
    results =[]
    for dataframe in array_df:
        mp = MarketProfile(dataframe)
        mp_slice = mp[dataframe.index.min():dataframe.index.max()]

        date = dataframe['Datetime'].iloc[0].strftime('%Y-%m-%d')  # Converti in formato data stringa
        mp_poc = mp_slice.poc_price
        mp_val_area_low, mp_val_area_high = mp_slice.value_area

        result = {
            'date': date,
            'mp_poc': mp_poc,
            'mp_val_area_low': mp_val_area_low,
            'mp_val_area_high': mp_val_area_high
        }
        results.append(result)
    return results

def mp_finder(index="SP500"):
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
##############################################################################################
                if not {'Datetime', 'High', 'Low', 'Open', 'Close', 'Volume'}.issubset(data.columns):
                    raise ValueError(
                        "Il DataFrame deve contenere le colonne 'Date', 'High', 'Low', 'Open', 'Close' e 'Volume'.")

                dfs_last_5_day = df_last_5_days(df=data)

                # results = return_market_profile(dfs_last_5_day)
                results = []
                for dataframe in dfs_last_5_day:
                    mp = MarketProfile(dataframe)
                    mp_slice = mp[data.index.min():data.index.max()]

                    date = dataframe['Datetime'].iloc[0].strftime('%Y-%m-%d')  # Converti in formato data stringa
                    mp_poc = mp_slice.poc_price
                    mp_val_area_low, mp_val_area_high = mp_slice.value_area

                    result={
                        'date': date,
                        'mp_poc': mp_poc,
                        'mp_val_area_low': mp_val_area_low,
                        'mp_val_area_high': mp_val_area_high
                    }
                    results.append(result)

                ind = len(results) - 1
                while ind > 0:
                    current_entry = results[ind]
                    previous_entry = results[ind - 1]

                    # Calcola l'overlap tra le due aree
                    current_interval = (current_entry["mp_val_area_low"], current_entry["mp_val_area_high"])
                    previous_interval = (previous_entry["mp_val_area_low"], previous_entry["mp_val_area_high"])
                    overlap = calculate_overlap(current_interval, previous_interval)

                    # Se l'overlap è almeno del 60%, unisci i dataframe corrispondenti e ricalcola il market profile
                    if overlap >= 0.6 * (current_interval[1] - current_interval[0]):
                        combined_df = pd.concat([dfs_last_5_day[ind - 1], dfs_last_5_day[ind]])
                        new_profile = MarketProfile(combined_df)
                        new_profile_slice = new_profile[data.index.min():data.index.max()]
                        dfs_last_5_day.pop(ind)
                        dfs_last_5_day.pop(ind - 1)
                        dfs_last_5_day.append(combined_df)
                        date_range = [previous_entry["date"], current_entry["date"]]
                        dizionario= {
                            'date': date_range,
                            'mp_poc': new_profile_slice.poc_price,
                            'mp_val_area_low': new_profile_slice.value_area[0],
                            'mp_val_area_high': new_profile_slice.value_area[1]
                        }
                        del results[ind]
                        del results[ind -1]
                        results.insert(ind-1, dizionario)
                    ind -= 1

                # Salva i risultati in un file JSON
                # Percorso completo del file
                file_path = f"{source_directory}/Data/{index}/5_mp/{item}_result.json"

                # Estrai la cartella padre dal percorso del file
                directory = os.path.dirname(file_path)

                # Se la cartella non esiste, creala
                if not os.path.exists(directory):
                    os.makedirs(directory)

                # Ora puoi aprire il file
                with open(file_path, 'w') as f:
                    json.dump(results, f, indent=4)

            except FileNotFoundError:
                print(f"File non trovato per {item}")
            except Exception as e:
                print(f"Errore durante l'elaborazione di {item}: {e}")

        file_report = report.save_report(filename=f"{index}_vwap_analysis")
        print(f"Report salvato in: {file_report}")
        duration = time.time() - start_time
        print(f"Tempo di esecuzione: {duration:.2f} secondi")
################################################################################################


if __name__ == '__main__':
    mp_finder(index = "Nasdaq")
    mp_finder(index = "SP500")
    #vwap_stock_finder(index="Russel")