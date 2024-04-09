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

                results = []
                for dataframe in dfs_last_5_day:
                    mp = MarketProfile(dataframe)
                    mp_slice = mp[data.index.min():data.index.max()]

                    date = dataframe['Datetime'].iloc[0].strftime('%Y-%m-%d')  # Converti in formato data stringa
                    mp_poc = mp_slice.poc_price
                    mp_val_area_low, mp_val_area_high = mp_slice.value_area

                    result=  {
                        'date': date,
                        'mp_poc': mp_poc,
                        'mp_val_area_low': mp_val_area_low,
                        'mp_val_area_high': mp_val_area_high
                    }
                    results.append(result)

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
            #     last_close_price = data['Close'].iloc[-1]
            #     vwap_values = []
            #     std_devs = []
            #
            #     # Ottieni i dati per settimana, mese, quadrimestre e anno
            #     timeframes = [
            #         ('Venerdì precedente', trading_vwap.get_previous_friday_vwap_and_std()),
            #         ('Ultimo giorno del mese precedente', trading_vwap.get_last_month_vwap_and_std()),
            #         ('Ultimo giorno del quadrimestre precedente', trading_vwap.get_last_quarter_vwap_and_std()),
            #         ('Ultimo giorno utile dell\'anno precedente', trading_vwap.get_last_year_vwap_and_std())
            #     ]
            #
            #     # Controlla la vicinanza del prezzo di chiusura ai valori VWAP
            #     for label, (vwap, std) in timeframes:
            #         vwap_minus_std, vwap_plus_std = vwap - std, vwap + std
            #
            #         if abs(last_close_price - vwap_minus_std) <= threshold or \
            #                 abs(last_close_price - vwap) <= threshold or \
            #                 abs(last_close_price - vwap_plus_std) <= threshold:
            #             close_to_vwap_stocks.append((item, label))
            #             exit_values = [vwap_minus_std, vwap, vwap_plus_std]
            #             image = CandlestickChartGenerator(data)
            #             image_path = image.create_chart_with_horizontal_lines_and_volume(lines=exit_values,
            #                                                                              max_points=90)
            #             report.add_content(f'Stock = {item} vicino al VWAP del {label}\n')
            #             report.add_commented_image(df=data, comment=f'VWAP values = {exit_values}\n',
            #                                        image_path=image_path)
            #             break
            #
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
    # mp_finder(index = "SP500")
    #vwap_stock_finder(index="Russel")