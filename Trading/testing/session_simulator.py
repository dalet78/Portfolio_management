import pandas as pd
from datetime import datetime, timedelta
import time
from support.logger import LoggerSingleton
from Trading.strategies_order.vwap_trading_strategies.vwap_diff_trading import check_vwap_diff_signal
from Trading.strategies_order.vwap_trading_strategies.vwap_diff_trading_with_rsi import check_vwap_diff_signal_with_rsi

STOCK_SYMBOL = "HST"  # Definisci lo stock symbol come costante globale

def load_and_shift_last_two_days(stock: str, data_path: str) -> pd.DataFrame:
    """
    Carica il file storico e shift solo gli ultimi due giorni per farli sembrare oggi e ieri.
    """
    data_filepath = f"{data_path}/{stock}_historical_data.csv"
    df = pd.read_csv(data_filepath, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True)

    # Trova le ultime due date disponibili
    df['date_only'] = df.index.date
    unique_dates = sorted(df['date_only'].unique())

    if len(unique_dates) < 2:
        raise ValueError(f"⚠️ Il file per {stock} ha meno di due giorni distinti di dati.")

    # Prendi le ultime due
    last_two_dates = unique_dates[-2:]

    # Filtra solo i dati degli ultimi due giorni
    df_filtered = df[df['date_only'].isin(last_two_dates)].copy()
    df_filtered.drop(columns=['date_only'], inplace=True)

    # Mappa i due giorni a oggi e ieri
    today = datetime.now().date()
    date_mapping = {
        last_two_dates[-2]: today - timedelta(days=1),
        last_two_dates[-1]: today,
    }

    # Shift degli index per visualizzare i dati come se fossero oggi e ieri
    df_filtered.index = [
        datetime.combine(date_mapping[dt.date()], dt.time())
        for dt in df_filtered.index
    ]

    return df_filtered


def simulate_intraday_session(df: pd.DataFrame, callback):
    """
    Simula una sessione live, riga per riga, con sleep di 1 secondo tra ogni step.

    Args:
        df (pd.DataFrame): DataFrame con dati shiftati (come se fossero oggi)
        callback (callable): funzione che riceve un sotto-df (fino al punto attuale)
    """
    # Filtra per i dati odierni e quelli del giorno precedente
    df = df.sort_index()

    # Trova la prima candela del giorno corrente
    today = datetime.now().date()
    df_today = df[df.index.date == today]

    # Elenco completo che include sia ieri che oggi
    df_yesterday = df[df.index.date < today]

    print(f"Simulating intraday session for {STOCK_SYMBOL}:")  # Stampa lo stock una volta

    # Esegui il loop sui dati, iniziando dalla prima candela di oggi
    for i in range(1, len(df_today) + 1):
        current_df = pd.concat([df_yesterday, df_today.iloc[:i] ], axis=0)  # Include tutto fino a quel punto
        callback(current_df)  # Chiama la tua logica (es. check_vwap_diff_signal)
        time.sleep(1)  # Simula il passare del tempo di 1 secondo tra le righe


def handle_live_data(df_chunk):
    result = check_vwap_diff_signal_with_rsi(df_chunk, stock=STOCK_SYMBOL, log=logger, trade_tracker=None)
    print(f"[{df_chunk.index[-1]}] Signal: {result['signal']} → {result.get('reason', '')}")


# Genera dinamicamente il percorso del file di log
daily_date = datetime.now().strftime("%d_%m_%y__%H_%M")
log_path = f"/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/daily_tading_{daily_date}_simulation.log"

# Inizializza il logger con il percorso del file
logger = LoggerSingleton.get_logger(log_file=log_path)


DATA_DIRECTORY = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
ALL_DATA_PATH = f"{DATA_DIRECTORY}/Data/TEST/5min"

df_shifted = load_and_shift_last_two_days(STOCK_SYMBOL, ALL_DATA_PATH)
print(df_shifted.head())

simulate_intraday_session(df_shifted, handle_live_data)