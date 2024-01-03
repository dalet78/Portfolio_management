import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import json
from libs.filtered_stock import return_filtred_list
from datetime import time
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
                stop_loss = low - 0.15  # SL sotto il prezzo corrente
                take_profit = self.vwap[-1]  # TP al VWAP
                self.buy(sl=stop_loss, tp=take_profit)

            # Se il segnale è di vendita
            elif self.signal[-1] == -1:
                # Imposta stop loss e take profit per la vendita
                stop_loss = high + 0.15  # SL sopra il prezzo corrente
                take_profit = self.vwap[-1]  # TP al VWAP
                self.sell(sl=stop_loss, tp=take_profit)

def Asaf_trading(index = "SP500"):
    global df
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"

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

                    if df["Close"].iloc[-1]>30:
                        df['numeric_signal'] = np.where(df['High_vwap_diff'] >= 0.35, -1,
                                                        np.where(df['Low_vwap_diff'] <= -0.35, 1, 0))
                    # Identifica i segnali
                    else:
                        df['numeric_signal'] = np.where(df['High_vwap_diff'] >= 0.20, -1,
                                   np.where(df['Low_vwap_diff'] <= -0.20, 1, 0))

                    # Esegui il backtesting
                    bt = Backtest(df, HOLCStrategy, cash=10000, commission=.002,
                                exclusive_orders = True)
                    stats = bt.run()

                    total_trades = stats['_trades'].shape[0]
                    win_rate = stats['Win Rate [%]']

                    # Controlla se il stock soddisfa i criteri
                    if total_trades > 3 and win_rate > 20:
                        # Salva il grafico in una variabile
                        fig = bt.plot()

                        # Aggiungi il nome dello stock come titolo del grafico
                        print(f'Performance del Backtest per {item} (Win Rate: {win_rate}%)')




                except FileNotFoundError:
                # Gestisci l'errore se il file non viene trovato
                    print(f"File non trovato per {item}")
                except Exception as e:
                # Gestisci altri errori generici
                    print(f"Errore durante l'elaborazione di {item}: {e}")

# Preparazione per il backtesting
if __name__ == "__main__":
    Asaf_trading(index="Nasdaq")
    #Asaf_trading(index="Russel")
    Asaf_trading(index="SP500")

