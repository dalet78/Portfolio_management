from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
import pandas as pd
import time
from libs.indicators.vwap_handler import  TradingVWAP
from libs.indicators.vmp_association_handler import *
from libs.filtered_stock import return_filtred_list

def vwap_stock_finder(index="Russel"):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Possible vwap stock")
    # Inizializza il dizionario JSON
    json_data = {"stocks": []}

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
            stock_data = {
                "name": item,
                "marketProfiles": {},  # Puoi aggiungere i dati del market profile qui
                "VWAPs": {}
            }
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv",
                                   parse_dates=['Date'])
##############################################################################################
                if not {'Date', 'High', 'Low', 'Open', 'Close', 'Volume'}.issubset(data.columns):
                    raise ValueError(
                        "Il DataFrame deve contenere le colonne 'Date', 'High', 'Low', 'Open', 'Close' e 'Volume'.")

                
                # threshold = 0.2
                trading_vwap = TradingVWAP(data)
                # last_close_price = data['Close'].iloc[-1]
                # vwap_values = []
                # std_devs = []

                # Ottieni i dati per settimana, mese, quadrimestre e anno
                # timeframes = [
                #     ('Venerdì precedente', trading_vwap.get_previous_friday_vwap_and_std()),
                #     ('Ultimo giorno del mese precedente', trading_vwap.get_last_month_vwap_and_std()),
                #     ('Ultimo giorno del quadrimestre precedente', trading_vwap.get_last_quarter_vwap_and_std()),
                #     ('Ultimo giorno utile dell\'anno precedente', trading_vwap.get_last_year_vwap_and_std())
                # ]

                # Calcola i VWAP e le deviazioni standard
                vwap_weekly, std_weekly = trading_vwap.get_previous_friday_vwap_and_std()
                vwap_monthly, std_monthly = trading_vwap.get_last_month_vwap_and_std()
                vwap_quarterly, std_quarterly = trading_vwap.get_last_quarter_vwap_and_std()

                data_filepath = f"{source_directory}/Data/SP500/5min/{item}_historical_data.csv"

                # Carica i dati
                df = load_data(data_filepath)
                # Controllo VMP e aggiunge VMP line nel json file
                dfs_per_day = split_data_by_day(df)

                # Calcola i valori di market profile per ogni giorno
                market_profile_values = calculate_market_profile_values(dfs_per_day)

                # Imposta la soglia di sovrapposizione
                overlap_threshold = 60  # Soglia percentuale per la sovrapposizione

                # Esegui l'iterazione per unire i DataFrame
                dfs_per_day_merged, merged_market_profile_values= iterative_merge_dfs(dfs_per_day, overlap_threshold)

                # Filtra i valori di market profile basandoti sulla lunghezza del DataFrame associato
                filtered_market_profiles = [
                    mp for df, mp in zip(dfs_per_day_merged, merged_market_profile_values) if len(df) >= 234
                ]

                for profile in filtered_market_profiles:
                    if 'Date' in profile:
                        del profile['Date']

                # Struttura per memorizzare i dati di uno stock
                stock_data = {
                    "name": item,
                    "marketProfiles": filtered_market_profiles,  # Aggiungi qui i dati del market profile se necessario
                    "VWAPs": {
                        "weekly": {
                            "VAL": round(vwap_weekly - std_weekly, 2),
                            "POC": round(vwap_weekly, 2),
                            "VAH": round(vwap_weekly + std_weekly, 2)
                        },
                        "monthly": {
                            "VAL": round(vwap_monthly - std_monthly, 2),
                            "POC": round(vwap_monthly, 2),
                            "VAH": round(vwap_monthly + std_monthly, 2)
                        },
                        "quarterly": {
                            "VAL": round(vwap_quarterly - std_quarterly, 2),
                            "POC": round(vwap_quarterly, 2),
                            "VAH": round(vwap_quarterly + std_quarterly, 2)
                        }
                    }
                }
                # Converti i valori di market profile in un DataFrame per una migliore visualizzazione
                values_df = pd.DataFrame(market_profile_values)

                # Controlla la vicinanza del prezzo di chiusura ai valori VWAP
                # for label, (vwap, std) in timeframes:
                #     vwap_minus_std, vwap_plus_std = vwap - std, vwap + std

                #     if abs(last_close_price - vwap_minus_std) <= threshold or \
                #             abs(last_close_price - vwap) <= threshold or \
                #             abs(last_close_price - vwap_plus_std) <= threshold:
                #         close_to_vwap_stocks.append((item, label))
                #         exit_values = [vwap_minus_std, vwap, vwap_plus_std]
                #         image = CandlestickChartGenerator(data)
                #         image_path = image.create_chart_with_horizontal_lines_and_volume(lines=exit_values,
                #                                                                          max_points=90)
                #         report.add_content(f'Stock = {item} vicino al VWAP del {label}\n')
                #         report.add_commented_image(df=data, comment=f'VWAP values = {exit_values}\n',
                #                                    image_path=image_path)
                #         break
                # Aggiungi i dati dello stock al JSON
                json_data["stocks"].append(stock_data)

            except FileNotFoundError:
                print(f"File non trovato per {item}")
            except Exception as e:
                print(f"Errore durante l'elaborazione di {item}: {e}")

            file_report = report.save_report(filename=f"{index}_vwap_analysis")
            print(f"Report salvato in: {file_report}")
            duration = time.time() - start_time
            print(f"Tempo di esecuzione: {duration:.2f} secondi")

        #save json in file
        with open(f'{source_directory}/Data/{index}_stocks_vwap_data.json', 'w') as f:
            json.dump(json_data, f, indent=4)
################################################################################################


def find_close_market_profile_values(index="SP500"):
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    # Lista per tenere traccia dei risultati
    close_values = []
    with open(f'{source_directory}/Data/{index}_stocks_vwap_data.json', 'r') as f:
        stock_data = json.load(f)

    for stock in stock_data["stocks"]:
        # Ottiene i valori di market profile e VWAP per lo stock corrente
        market_profiles = stock["marketProfiles"]
        vwap_values = stock["VWAPs"]

        # Scorre attraverso i valori di market profile
        for mp in market_profiles:
            # Confronta con ogni periodo di VWAP (weekly, monthly, quarterly)
            for period, vwap in vwap_values.items():
                # Calcola la differenza e verifica se è inferiore o uguale a 0.05
                if abs(mp["VAL"] - vwap["VAL"]) <= 0.05 or \
                   abs(mp["POC"] - vwap["POC"]) <= 0.05 or \
                   abs(mp["VAH"] - vwap["VAH"]) <= 0.05:
                    close_values.append({
                        "stock": stock["name"],
                        "marketProfile": mp,
                        "vwapPeriod": period,
                        "vwapValues": vwap
                    })

    return close_values

def find_stock_near_congruence(congruence_list):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"sp500 Possible CONGRUENCE stock")
    for stock in congruence_list['stocks']:
        item = stock['name']
        print(f'Analyze stock = {item}')
        try:
            data = pd.read_csv(f"{source_directory}/Data/sp500/Daily/{item}_historical_data.csv",
                               parse_dates=['Date'])
            data['Close'].iloc[-1]

        except FileNotFoundError:
            print(f"File non trovato per {item}")
        except Exception as e:
            print(f"Errore durante l'elaborazione di {item}: {e}")


if __name__ == '__main__':
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    #vwap_stock_finder(index = "Nasdaq")
    #vwap_stock_finder(index = "SP500")
    #vwap_stock_finder(index="Russel")
    congruence_list_nasdaq = find_close_market_profile_values(index = "Nasdaq")
    congruence_list_SP500 = find_close_market_profile_values(index="SP500")
    # save json in file
    with open(f'{source_directory}/Data/Nasdaq_stocks_cong_data.json', 'w') as f:
        json.dump(congruence_list_nasdaq, f, indent=4)
    with open(f'{source_directory}/Data/SP500_stocks_cong_data.json', 'w') as f:
        json.dump(congruence_list_SP500, f, indent=4)

