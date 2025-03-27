import os
import pandas as pd
from libs.filtered_stock import return_filtred_list
from support.data_preparation import DataRefactory
from libs.level_creation.vwap_calc import VWAPCalculator
from libs.level_creation.dbscan_level import DBSCANLevels


# Costanti
DATA_DIRECTORY = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
ALL_DATA_PATH = f"{DATA_DIRECTORY}/Data/ALL/5min"
REPORT_DIRECTORY = f"{DATA_DIRECTORY}/Reports/Data"
REPORT_FILEPATH = f"{REPORT_DIRECTORY}/vwap_resistance_results.csv"

# Creazione della directory dei report se non esiste
os.makedirs(REPORT_DIRECTORY, exist_ok=True)

filtered_stocks = return_filtred_list(index="ALL")


def calculate_vwap_and_resistances(stock, eps=0.1, min_samples=2):
    """
    Calcola il VWAP e le resistenze per uno stock specifico.
    """
    file_path = f"{ALL_DATA_PATH}/{stock}_historical_data.csv"
    if not os.path.exists(file_path):
        print(f"Dati non trovati per {stock}")
        return None

    print(f"Analizzo dati {stock}")
    # Caricare i dati
    df =DataRefactory.prepare_5m_csv(filepath=file_path)
    # Rimuovere il timezone dalla colonna Datetime
    df.reset_index(inplace=True)
    df['Datetime'] = pd.to_datetime(df['Datetime']).dt.tz_localize(None)

    # Eliminare le colonne non necessarie
    df = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df= df.tail(26208)

    # Calcolare il VWAP
    vwap_calc = VWAPCalculator(df)
    df_vwap = vwap_calc.calculate_vwap_daily()

    # Identificare livelli di resistenza
    dbscan_levels = DBSCANLevels(df, percentage_eps=eps, min_samples=min_samples)
    resistances = dbscan_levels.find_levels()
    resistances = [round(r, 2) for r in resistances]
    return {
        "Stock": stock,
        "VWAP": df_vwap[['Datetime', 'VWAP']].tail(1).to_dict(orient='records'),
        "Resistances": resistances
    }


def process_all_stocks():
    """
    Calcola il VWAP e le resistenze per tutti gli stock filtrati.
    """
    results = []
    for stock in filtered_stocks:
        result = calculate_vwap_and_resistances(stock)
        if result:
            results.append(result)

    # Salva i risultati in un CSV
    df_results = pd.DataFrame(results)
    df_results.to_csv(REPORT_FILEPATH, index=False)
    print(f"Risultati salvati in {REPORT_FILEPATH}")


# Esegui il calcolo per tutti gli stock
if __name__ == "__main__":
    process_all_stocks()