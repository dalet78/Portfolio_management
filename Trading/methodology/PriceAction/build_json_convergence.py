from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
from datetime import date
from libs.indicators.vwap_handler import  TradingVWAP
from libs.indicators.vmp_association_handler import *
from libs.filtered_stock import return_filtred_list

def vwap_stock_finder(index="Russel"):

    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    # Inizializza il dizionario JSON
    json_data = {"stocks": []}

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    tickers_list = return_filtred_list(index=index)
    close_to_vwap_stocks = []
    # Controlla se la lista dei ticker è vuota
    if not tickers_list:
        # Aggiungi un messaggio nel report o registra un log
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
                data = data.rename(columns={'Date': 'Datetime'})
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
                #vwap_monthly, std_monthly = trading_vwap.get_last_month_vwap_and_std()
                vwap_quarterly, std_quarterly = trading_vwap.get_last_quarter_vwap_and_std()

                data_filepath = f"{source_directory}/Data/SP500/5min/{item}_historical_data.csv"

                # Carica i dati
                df = load_data(data_filepath)
                # Controllo VMP e aggiunge VMP line nel json file
                dfs_per_day = split_data_by_day(df)
                trading_vwap_daily = TradingVWAP(df)
                vwap_daily, std_daily = trading_vwap_daily.get_daily_vwap_with_deviation()


                # Calcola i valori di market profile per ogni giorno
                market_profile_values = calculate_market_profile_values(dfs_per_day)

                # Imposta la soglia di sovrapposizione
                overlap_threshold = 60  # Soglia percentuale per la sovrapposizione

                # # Esegui l'iterazione per unire i DataFrame
                # dfs_per_day_merged, merged_market_profile_values= iterative_merge_dfs(dfs_per_day, overlap_threshold)

                # # Filtra i valori di market profile basandoti sulla lunghezza del DataFrame associato
                # filtered_market_profiles = [
                #     mp for df, mp in zip(dfs_per_day_merged, merged_market_profile_values) if len(df) >= 234
                # ]

                # for profile in filtered_market_profiles:
                #     if 'Date' in profile:
                #         del profile['Date']
                last_df1, last_mp_comp1, last_df2, last_mp2 = get_last_and_longest_dfs(dfs_per_day, overlap_threshold)
                last_df= [dfs_per_day[-1]]
                last_mp1 = calculate_market_profile_values(last_df)
                filtered_market_profiles= [last_mp1, last_mp_comp1]

                # Struttura per memorizzare i dati di uno stock
                stock_data = {
                    "name": item,
                    "marketProfiles": filtered_market_profiles,  
                    "VWAPs": {
                        "weekly": {
                            "VAL": round(vwap_weekly - std_weekly, 2),
                            "POC": round(vwap_weekly, 2),
                            "VAH": round(vwap_weekly + std_weekly, 2)
                        },
                        "daily": {
                            "VAL": round(vwap_daily - std_daily, 2),
                            "POC": round(vwap_daily, 2),
                            "VAH": round(vwap_daily + std_daily, 2)
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



        #save json in file
        file_path = f'{source_directory}/Data/{index}_stocks_vwap_data.json'

        # Scrivi il file JSON con la funzione di serializzazione personalizzata
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=4, default=serialize_date)
################################################################################################



# Funzione di serializzazione personalizzata per oggetti datetime.date
def serialize_date(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError("Type not serializable")


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
        if market_profiles is not None and vwap_values is not None:
            for mp_list in market_profiles:
                if mp_list is not None and isinstance(mp_list, list):
                    for mp in mp_list:
                        # Verifica se mp è un dizionario prima di accedere alle chiavi
                        if isinstance(mp, dict):
                            for period, vwap in vwap_values.items():
                                for mp_type in ["VAL", "POC", "VAH"]:
                                    if mp_type in mp and isinstance(mp[mp_type],
                                                                    (int, float)) and mp_type in vwap and isinstance(
                                            vwap[mp_type], (int, float)):
                                        if abs(mp[mp_type] - vwap[mp_type]) <= 0.05:
                                            close_values.append({
                                                "stock": stock["name"],
                                                "mp_type": mp_type,
                                                "mp": mp[mp_type],
                                                "vwapPeriod": period,
                                                "vwap_type": mp_type,
                                                "vwap": vwap[mp_type]
                                            })

    # save json in file
    with open(f'{source_directory}/Data/{index}_stocks_cong_data.json', 'w') as f:
        json.dump(close_values, f, indent=4)

# def find_close_market_profile_values(index="SP500"):
#     source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
#     # Lista per tenere traccia dei risultati
#     close_values = []
#     with open(f'{source_directory}/Data/{index}_stocks_vwap_data.json', 'r') as f:
#         stock_data = json.load(f)
#
#     for stock in stock_data["stocks"]:
#         # Ottiene i valori di market profile e VWAP per lo stock corrente
#         market_profiles = stock["marketProfiles"]
#         vwap_values = stock["VWAPs"]
#
#         # Scorre attraverso i valori di market profile
#         for mp in market_profiles:
#             # Confronta con ogni periodo di VWAP (weekly, monthly, quarterly)
#             for period, vwap in vwap_values.items():
#                 # Calcola la differenza e verifica se è inferiore o uguale a 0.05
#                 if abs(mp["VAL"] - vwap["VAL"]) <= 0.05:
#                     close_values.append({
#                         "stock": stock["name"],
#                         "mp_type" : "VAL",
#                         "mp": mp["VAL"],
#                         "vwapPeriod": period,
#                         "vwap_type": "VAL",
#                         "vwap": vwap["VAL"]
#                     })
#                 elif abs(mp["VAL"] - vwap["POC"]) <= 0.05:
#                     close_values.append({
#                         "stock": stock["name"],
#                         "mp_type": "VAL",
#                         "mp": mp["VAL"],
#                         "vwapPeriod": period,
#                         "vwap_type": "POC",
#                         "vwap": vwap["POC"]
#                     })
#                 elif abs(mp["VAL"] - vwap["VAH"]) <= 0.05:
#                     close_values.append({
#                         "stock": stock["name"],
#                         "mp_type": "VAL",
#                         "mp": mp["VAL"],
#                         "vwapPeriod": period,
#                         "vwap_type": "VAH",
#                         "vwap": vwap["VAH"]
#                     })
#                 elif abs(mp["POC"] - vwap["VAL"]) <= 0.05:
#                     close_values.append({
#                         "stock": stock["name"],
#                         "mp_type": "POC",
#                         "mp": mp["POC"],
#                         "vwapPeriod": period,
#                         "vwap_type": "VAL",
#                         "vwap": vwap["VAL"]
#                     })
#                 elif abs(mp["POC"] - vwap["POC"]) <= 0.05:
#                     close_values.append({
#                         "stock": stock["name"],
#                         "mp_type": "POC",
#                         "mp": mp["POC"],
#                         "vwapPeriod": period,
#                         "vwap_type": "VAL",
#                         "vwap": vwap["POC"]
#                     })
#                 elif abs(mp["POC"] - vwap["VAH"]) <= 0.05:
#                     close_values.append({
#                         "stock": stock["name"],
#                         "mp_type": "POC",
#                         "mp": mp["POC"],
#                         "vwapPeriod": period,
#                         "vwap_type": "VAL",
#                         "vwap": vwap["VAH"]
#                     })
#                 elif abs(mp["VAH"] - vwap["VAL"]) <= 0.05:
#                     close_values.append({
#                         "stock": stock["name"],
#                         "mp_type": "VAH",
#                         "mp": mp["VAH"],
#                         "vwapPeriod": period,
#                         "vwap_type": "VAL",
#                         "vwap": vwap["VAL"]
#                     })
#                 elif abs(mp["VAH"] - vwap["POC"]) <= 0.05:
#                     close_values.append({
#                         "stock": stock["name"],
#                         "mp_type": "VAH",
#                         "mp": mp["VAH"],
#                         "vwapPeriod": period,
#                         "vwap_type": "VAL",
#                         "vwap": vwap["POC"]
#                     })
#                 elif abs(mp["VAH"] - vwap["VAH"]) <= 0.05:
#                     close_values.append({
#                         "stock": stock["name"],
#                         "mp_type": "VAH",
#                         "mp": mp["VAH"],
#                         "vwapPeriod": period,
#                         "vwap_type": "VAL",
#                         "vwap": vwap["VAH"]
#                     })
#     # save json in file
#     with open(f'{source_directory}/Data/{index}_stocks_cong_data.json', 'w') as f:
#         json.dump(close_values, f, indent=4)
#

def find_stock_near_congruence(index= "SP500"):
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    with open(f'{source_directory}/Data/{index}_stocks_cong_data.json', 'r') as f:
            stock_data = json.load(f)
    report = ReportGenerator()
    report.add_title(title=f"{index} Possible CONGRUENCE stock")
    threshold_value = 0.02
    for item in stock_data:
        item_data = item["stock"]
        data_filepath = f"{source_directory}/Data/{index}/5min/{item_data}_historical_data.csv"
        # Carica i dati
        df = load_data(data_filepath)
        if abs(df["Close"].iloc[-1]-item["mp"])<= threshold_value*df["Close"].iloc[-1]:
            image = CandlestickChartGenerator(df)
            image_path = image.create_chart_with_areas(item, max_points=180)
            report.add_content(f'stock = {item_data} - vwap type = {item["vwapPeriod"]}\n')
            report.add_commented_image(df=df, comment=f'market_profile={item["mp_type"]} - {item["mp"]} '
                                                      f'vwap_values={item["vwap_type"]} - {item["vwap"]} '
                                                      , image_path=image_path)
        
    file_report = report.save_report(filename=f"{index}_convergence_stock")
    return file_report
    
def find_convergense_value(index="Nasdaq"):
    vwap_stock_finder(index=index)
    find_close_market_profile_values(index=index)
    report_file = find_stock_near_congruence(index=index)
    return report_file

if __name__ == '__main__':
    #start_time = time.time()  # Registra l'ora di inizio
    #source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    #vwap_stock_finder(index = "Nasdaq")
    #vwap_stock_finder(index = "SP500")
    #vwap_stock_finder(index="Russel")
    find_close_market_profile_values(index="Nasdaq")
    find_close_market_profile_values(index="SP500")
    find_stock_near_congruence(index="Nasdaq")
    find_stock_near_congruence(index="SP500")
    #duration = time.time() - start_time
    #print(f"Tempo di esecuzione: {duration:.2f} secondi")
    
    
    

