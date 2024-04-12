import json
import os
import pandas as pd
import time
from market_profile import MarketProfile
from libs.filtered_stock import return_filtred_list


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

def mp_finder(index="SP500"):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    tickers_list = return_filtred_list(index=index)
    close_to_vwap_stocks = []

    if not tickers_list:
        print("Nessun ticker soddisfa i criteri di selezione.")
        return

    for item in tickers_list:
        print(f'Analyze stock = {item}')
        result = False
        try:
            data = pd.read_csv(f"{source_directory}/Data/{index}/5min/{item}_historical_data.csv",
                               parse_dates=['Datetime'])
            dfs_last_5_day = df_last_5_days(df=data)

            results = []
            for dataframe in dfs_last_5_day:
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

            # Cerca sovrapposizioni tra due elementi consecutivi
            for i in range(len(results) - 1, 0, -1):
                current_entry = results[i]
                previous_entry = results[i - 1]

                # Calcola l'overlap tra le due aree
                current_interval = (current_entry["mp_val_area_low"], current_entry["mp_val_area_high"])
                previous_interval = (previous_entry["mp_val_area_low"], previous_entry["mp_val_area_high"])
                overlap = calculate_overlap(current_interval, previous_interval)

                # Se l'overlap è almeno del 60%, unisci i dataframe corrispondenti e ricalcola il market profile
                if overlap >= 0.6 * (current_interval[1] - current_interval[0]):
                    combined_df = pd.concat([dfs_last_5_day[i - 1], dfs_last_5_day[i]])
                    new_profile = MarketProfile(combined_df)
                    dfs_last_5_day.pop(i)
                    dfs_last_5_day.pop(i - 1)
                    dfs_last_5_day.append(combined_df)
                    date_range = [previous_entry["date"], current_entry["date"]]
                    new_result = {
                        'date': date_range,
                        'mp_poc': new_profile.poc_price,
                        'mp_val_area_low': new_profile.value_area[0],
                        'mp_val_area_high': new_profile.value_area[1]
                    }
                    break
            else:
                new_result = results

            file_path = f"{source_directory}/Data/{index}/5_mp/{item}_result.json"
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(file_path, 'w') as f:
                json.dump(new_result, f, indent=4)
        except FileNotFoundError:
            print(f"File non trovato per {item}")
        except Exception as e:
            print(f"Errore durante l'elaborazione di {item}: {e}")

    duration = time.time() - start_time
    print(f"Tempo di esecuzione: {duration:.2f} secondi")


if __name__ == '__main__':
    mp_finder(index="Nasdaq")
