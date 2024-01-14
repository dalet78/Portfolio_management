import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import json
from libs.filtered_stock import return_filtred_list
from datetime import time
from Reports.report_builder import ReportGenerator
import matplotlib.pyplot as plt

def load_data(filepath):
    """Carica i dati dal file CSV."""
    df = pd.read_csv(filepath, parse_dates=['Datetime'])
    df.rename(columns={'Datetime': 'datetime'}, inplace=True)
    df.set_index('datetime', inplace=True)
    return df

class HOLCStrategy(Strategy):
    last_trade_date = None
    def init(self):
        global df  # Usa una variabile globale
        super().init()
        self.signal = self.I(lambda: df['numeric_signal'], name='numeric_signal')
        self.vwap = self.I(lambda: df['vwap'], name='vwap')


    def next(self):
        price = self.data.Close[-1]  # Prezzo attuale
        high = self.data.High[-1]
        low = self.data.Low[-1]
        current_time = self.data.index[-1].time()  # L'orario corrente dell'ultimo punto dati
        current_date = self.data.index[-1].date()  # La data corrente dell'ultimo punto dati

        entry_start_time = time(10, 00)  # 10:00 AM
        entry_end_time = time(12, 00)  # 12:00 PM
        exit_time = time(15, 50)  # 17:00 PM

        if self.position and current_time >= exit_time:
            self.position.close()
            self.last_trade_date = None  # Resettare la data dell'ultimo trade


        # Controlla se è il momento di aprire una nuova posizione
        elif (entry_start_time <= current_time <= entry_end_time and not self.position and
              (self.last_trade_date is None or self.last_trade_date != current_date)):

            # Fai un trade e aggiorna l'ultima data di trade

            self.last_trade_date = current_date

            # Se il segnale è di acquisto
            if self.signal[-1] == 1:
                # Imposta stop loss e take profit per l'acquisto
                take_profit = self.vwap[-1]  # TP al VWAP
                self.entry_price = price
                stop_loss = self.entry_price - abs(take_profit - self.entry_price)/2
                try:
                    self.buy(sl=stop_loss, tp=take_profit)
                except Exception as e:
                    pass

            # Se il segnale è di vendita
            elif self.signal[-1] == -1:
                # Imposta stop loss e take profit per la vendita
                take_profit = self.vwap[-1]  # TP al VWAP
                self.entry_price = price
                stop_loss = self.entry_price + abs(take_profit - self.entry_price) / 2
                try:
                    self.sell(sl=stop_loss, tp=take_profit)
                except Exception as e:
                    pass

def Asaf_trading(index = "SP500"):
    global df
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Optimization difference vwap strategy for stock")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

        tickers_list = return_filtred_list(index=index)
        # Controlla se la lista dei ticker è vuota
        if not tickers_list:
            # Aggiungi un messaggio nel report o registra un log

            print("Nessun ticker soddisfa i criteri di selezione.")
        else:

            for item in tickers_list:
                print(f'Analyze stock = {item}')
                try:
                    data_filepath = f"{source_directory}/Data/{index}/5min/{item}_historical_data.csv"
                    df = load_data(data_filepath)

                    # Calcola il prodotto di prezzo e volume, e il volume cumulativo
                    df['price_volume'] = df['Close'] * df['Volume']
                    # Raggruppa per giorno e calcola il VWAP cumulativo per ogni momento
                    # Il calcolo si resetta all'inizio di ogni nuovo giorno
                    df['cumulative_price_volume'] = df.groupby(df.index.normalize())['price_volume'].cumsum()
                    df['cumulative_volume'] = df.groupby(df.index.normalize())['Volume'].cumsum()
                    df['vwap'] = df['cumulative_price_volume'] / df['cumulative_volume']

                    # Resetta i valori cumulativi ogni giorno
                    #df['vwap'] = df.groupby(df.index.date)['price_volume'].transform('sum') / df.groupby(df.index.date)[
                       # 'Volume'].transform('sum')


                    # Calcola la differenza tra HOLC e VWAP
                    for col in ['Open', 'High', 'Low', 'Close']:
                        df[f'{col}_vwap_diff'] = df[col] - df['vwap']

                    best_high_vwap_diff, best_win_rate, total_trades = optimize_high_vwap_diff(df)
                    if best_win_rate > 40:
                        report.add_content(f"stock = {item}")
                        report.add_content(f"Optimal High_vwap_diff for {item}: {best_high_vwap_diff}")
                        report.add_content(f"Corresponding Win Rate: {best_win_rate}%")
                        report.add_content(f"total trade = {total_trades}\n")
                    print(f"Optimal High_vwap_diff for {item}: {best_high_vwap_diff}")
                    print(f"Corresponding Win Rate: {best_win_rate}% - total trade = {total_trades}")

                    # Usa best_high_vwap_diff per il trading o esegui altre azioni necessarie


                except FileNotFoundError:
                # Gestisci l'errore se il file non viene trovato
                    print(f"File non trovato per {item}")
                except Exception as e:
                # Gestisci altri errori generici
                    print(f"Errore durante l'elaborazione di {item}: {e}")
            file_report = report.save_report(filename=f"{index}_best_vwap_diff_stock")

def optimize_high_vwap_diff(df):
    best_high_vwap_diff = None
    best_win_rate = 0

    for high_vwap_diff_value in np.arange(0.20, 0.61, 0.05):  # 41 valori tra 0.20 e 0.60
        # Calcola il segnale in base a High_vwap_diff
        df['numeric_signal'] = np.where(df['High_vwap_diff'] >= high_vwap_diff_value, -1,
                                        np.where(df['Low_vwap_diff'] <= -high_vwap_diff_value, 1, 0))

        # Esegui il backtesting
        bt = Backtest(df, HOLCStrategy, cash=10000, commission=.002, exclusive_orders=True)
        stats = bt.run()

        total_trades = stats['_trades'].shape[0]
        win_rate = stats['Win Rate [%]']

        # Aggiorna il miglior win rate e il valore corrispondente di High_vwap_diff
        if total_trades > 3 and win_rate > best_win_rate:
            best_win_rate = win_rate
            best_high_vwap_diff = high_vwap_diff_value
            total_trade_best = total_trades

    return best_high_vwap_diff, best_win_rate, total_trade_best

# Preparazione per il backtesting
if __name__ == "__main__":
    Asaf_trading(index="Nasdaq")
    Asaf_trading(index="Russel")
    Asaf_trading(index="SP500")

