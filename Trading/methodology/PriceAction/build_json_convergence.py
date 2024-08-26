from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
from datetime import date
from libs.indicators.vwap_handler import  TradingVWAP
from libs.indicators.vmp_association_handler import *
from libs.filtered_stock import return_filtred_list
from Trading.methodology.PriceAction.build_market_profile import mp_finder

def vwap_stock_finder(index="Russel"):
    mp_finder(index=index)

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

                vwap_quarterly, std_quarterly = trading_vwap.get_last_quarter_vwap_and_std()

                data_filepath = f"{source_directory}/Data/{index}/5min/{item}_historical_data.csv"
                if not {'Datetime', 'High', 'Low', 'Open', 'Close', 'Volume'}.issubset(data.columns):
                    raise ValueError(
                        "Il DataFrame deve contenere le colonne 'Datetime', 'High', 'Low', 'Open', 'Close' e 'Volume'.")
                # Carica i dati
                df = load_data(data_filepath)
                # Controllo VMP e aggiunge VMP line nel json file
                # dfs_per_day = split_data_by_day(df)
                trading_vwap_daily = TradingVWAP(df)
                vwap_weekly, std_weekly = trading_vwap_daily.get_previous_friday_vwap_and_std()
                vwap_daily, std_daily = trading_vwap_daily.get_last_daily_vwap()

                # Struttura per memorizzare i dati di uno stock
                stock_data = {
                    "name": item,
                    "marketProfiles": "",
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
                file_path = f"{source_directory}/Data/{index}/5_mp/{item}_result.json"
                with open(file_path, 'r') as file:
                    market_profile_dict= json.load(file)
                stock_data['market_profile_dict'] = market_profile_dict
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

def find_stock_near_congruence(index= "SP500"):
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    with open(f'{source_directory}/Data/{index}_stocks_vwap_data.json', 'r') as f:
            stock_data = json.load(f)
    report = ReportGenerator()
    report.add_title(title=f"{index} Possible CONGRUENCE stock")
    threshold_value = 0.0
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

def create_file_report(index= "SP500"):
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    with open(f'{source_directory}/Data/{index}_stocks_vwap_data.json', 'r') as f:
        stock_data = json.load(f)
    report = ReportGenerator()
    report.add_title(title=f"{index} Area value")
    for item in stock_data["stocks"]:
        # Estrai i dati rilevanti
        name = item["name"]
        # Aggiungi il nome dello stock al report
        report.add_content(f"stock = {name}\n")
        # Aggiungi il vwap dello stock al report
        report.add_content(
            f"vwap daily = {item['VWAPs']['daily']['POC']} low ={item['VWAPs']['daily']['VAL']} high {item['VWAPs']['daily']['VAH']}\n")
        report.add_content(
            f"vwap weekly = {item['VWAPs']['weekly']['POC']} low ={item['VWAPs']['weekly']['VAL']} high {item['VWAPs']['weekly']['VAH']}\n")
        report.add_content(
            f"vwap quarter = {item['VWAPs']['quarterly']['POC']} low ={item['VWAPs']['quarterly']['VAL']} high {item['VWAPs']['quarterly']['VAH']}\n")
        market_profile_dict = item["market_profile_dict"]

        # Aggiungi il nome dello stock al report


        # Itera attraverso ogni voce nel market_profile_dict
        for profile in market_profile_dict:
            date = profile["date"]
            # Controlla se la data è composta
            if isinstance(date, list):
                # Aggiungi i dettagli del profilo al report
                report.add_content(
                    f'Date: {date}, POC: {profile["mp_poc"]}, VAL Low: {profile["mp_val_area_low"]}, VAL High: {profile["mp_val_area_high"]}\n')

            # Salva il report
    file_report = report.save_report(filename=f"{index}_convergence_stock")
    return file_report


def find_convergence_value(index="Nasdaq"):
    vwap_stock_finder(index=index)
    # find_close_market_profile_values(index=index)
    report_file = create_file_report(index=index)
    return report_file

if __name__ == '__main__':
    #start_time = time.time()  # Registra l'ora di inizio
    #source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    # vwap_stock_finder(index="Nasdaq")
    report = find_convergence_value(index = "SP500")
    # #vwap_stock_finder(index="Russel")
    # find_close_market_profile_values(index="Nasdaq")
    # find_close_market_profile_values(index="SP500")
    # find_stock_near_congruence(index="Nasdaq")
    # find_stock_near_congruence(index="SP500")
    #duration = time.time() - start_time
    #print(f"Tempo di esecuzione: {duration:.2f} secondi")
    
    
    

