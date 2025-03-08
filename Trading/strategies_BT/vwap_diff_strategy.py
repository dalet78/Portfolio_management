import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import json
from libs.filtered_stock import return_filtred_list
from datetime import time
from Reports.report_builder import ReportGenerator
from support.data_preparation import DataRefactory

# Strategy Parameters
ENTRY_START_TIME = time(16, 00)  # Entry start time (3:30 PM)
ENTRY_END_TIME = time(17, 30)    # Entry end time (5:30 PM)
EXIT_TIME = time(20, 50)         # Exit time (8:50 PM)
SL_PERCENT = 0.007 # Stop Loss percentage (0.5%)
TP_PERCENT = 0.014


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

        if self.position and current_time >= EXIT_TIME:
            self.position.close()
            self.last_trade_date = None  # Resettare la data dell'ultimo trade


        # Controlla se è il momento di aprire una nuova posizione
        elif (ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and not self.position and

              (self.last_trade_date is None or self.last_trade_date != current_date)):

            # Fai un trade e aggiorna l'ultima data di trade

            self.last_trade_date = current_date

            # Se il segnale è di acquisto
            if self.signal[-1] == 1:
                # Imposta stop loss e take profit per l'acquisto
                stop_loss = low - (SL_PERCENT* self.data.Close[-1])  # SL sotto il prezzo corrente
                take_profit = self.vwap[-1]  # TP al VWAP
                self.buy(sl=stop_loss, tp=take_profit)

            # Se il segnale è di vendita
            elif self.signal[-1] == -1:
                # Imposta stop loss e take profit per la vendita
                stop_loss = high + (SL_PERCENT* self.data.Close[-1])  # SL sopra il prezzo corrente
                take_profit = self.vwap[-1]  # TP al VWAP
                self.sell(sl=stop_loss, tp=take_profit)

def vwap_diff_trading(index = "SP500"):
    global df
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index}  VWAP distance calculation stock")
    report.add_content(f"Trading starts from 5:00 PM\n")
    # Strategy Description
    report.add_content(f"Strategy Description:\n")
    report.add_content(f"1. Timeframe: 5-minute candles\n")
    report.add_content(f"2. Entry window: {ENTRY_START_TIME} - {ENTRY_END_TIME}\n")
    report.add_content(f"3. Exit time: {EXIT_TIME}\n")
    report.add_content(
        f"4. Buy Condition: If the vwap difference is {TP_PERCENT * 100}%, buy with a Stop Loss of {SL_PERCENT * 100}% below the current price and Take Profit at the VWAP.\n")
    report.add_content(
        f"5. Sell Condition: If the difference is {TP_PERCENT * 100}% sell with a Stop Loss of {SL_PERCENT * 100}% above the current price and Take Profit at the VWAP.\n")
    report.add_content(
        f"6. Strategy operates within a daily time window, opening positions only once per day. Positions are closed at {EXIT_TIME}.\n")
    report.add_content(f"7. Take Profit: Set at the VWAP value, Stop Loss: {SL_PERCENT * 100}% of the current price.\n")


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
                    df = DataRefactory.prepare_5m_csv(filepath=data_filepath)

                    # Calcola il prodotto di prezzo e volume, e il volume cumulativo
                    df['price_volume'] = df['Close'] * df['Volume']
                    # Raggruppa per giorno e calcola il VWAP cumulativo per ogni momento
                    # Il calcolo si resetta all'inizio di ogni nuovo giorno
                    df['cumulative_price_volume'] = df.groupby(df.index.normalize())['price_volume'].cumsum()
                    df['cumulative_volume'] = df.groupby(df.index.normalize())['Volume'].cumsum()
                    df['vwap'] = df['cumulative_price_volume'] / df['cumulative_volume']


                    # Calcola la differenza tra HOLC e VWAP
                    for col in ['Open', 'High', 'Low', 'Close']:
                        df[f'{col}_vwap_diff'] = df[col] - df['vwap']

                    # if df["Close"].iloc[-1]>30:
                    df['numeric_signal'] = np.where(df['High_vwap_diff'] >= TP_PERCENT*df['Close'], -1,
                                                    np.where(df['Low_vwap_diff'] <= -(TP_PERCENT*df['Close']), 1, 0))
                    # Identifica i segnali
                    # else:
                    #     df['numeric_signal'] = np.where(df['High_vwap_diff'] >= 0.20, -1,
                    #                np.where(df['Low_vwap_diff'] <= -0.20, 1, 0))

                    # Esegui il backtesting
                    bt = Backtest(df, HOLCStrategy, cash=10000, commission=.002,
                                exclusive_orders = True)
                    stats = bt.run()

                    total_trades = stats['_trades'].shape[0]
                    win_rate = stats['Win Rate [%]']
                    sharpe_ratio = stats['Sharpe Ratio']
                    max_drawdown = stats['Max. Drawdown [%]']
                    total_return = stats['Return [%]']
                    cagr = stats['CAGR [%]']

                    # Controlla se il stock soddisfa i criteri
                    if total_trades > 3 and win_rate > 50:
                        # Salva il grafico in una variabile
                        fig = bt.plot()

                        # Aggiungi il nome dello stock come titolo del grafico
                        report.add_content(f"Stock = {item}")
                        report.add_content(f"Corresponding Win Rate: {win_rate}%")
                        report.add_content(f"Total Trades = {total_trades}")
                        report.add_content(f"Sharpe Ratio = {sharpe_ratio}")
                        report.add_content(f"Max Drawdown = {max_drawdown}%")
                        report.add_content(f"Total Return = {total_return}%")
                        report.add_content(f"CAGR = {cagr}%\n")

                        print(f'Performance del Backtest per {item} (Win Rate: {win_rate}%)')



                except FileNotFoundError:
                # Gestisci l'errore se il file non viene trovato
                    print(f"File non trovato per {item}")
                except Exception as e:
                # Gestisci altri errori generici
                    print(f"Errore durante l'elaborazione di {item}: {e}")
        file_report = report.save_report(filename=f"{index}_vwap_diff_stock")
        return file_report

# Preparazione per il backtesting
if __name__ == "__main__":
    vwap_diff_trading(index="ALL")


