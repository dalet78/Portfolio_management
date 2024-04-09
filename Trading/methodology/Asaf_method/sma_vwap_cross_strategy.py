import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
import json
from libs.filtered_stock import return_filtred_list
from datetime import time
import matplotlib.pyplot as plt
from Reports.report_builder import ReportGenerator
from Trading.methodology.PriceAction.sma_vwap_sr_support import SupportResistanceFinder

def load_data(filepath):
    """Carica i dati dal file CSV."""
    df = pd.read_csv(filepath, parse_dates=['Datetime'])
    df.rename(columns={'Datetime': 'datetime'}, inplace=True)
    df.set_index('datetime', inplace=True)
    return df

class HOLCStrategy(Strategy):
    last_trade_date = None
    def init(self):
        super().init()
        price = self.data.Close
        self.ma1 = self.I(SMA, price, 5)
        self.ma2 = self.I(SMA, price, 10)
        self.vwap = self.data.Daily_VWAP
        # print(df.head())

    def next(self):

        sma1 = self.ma1[-1]
        sma2 = self.ma2[-1]
        vwap = self.vwap[-1]
        candle_direction = "bullish" if self.data.Close[-1] > self.data.Open[-1] else "bearish"

        # Verifica il crossover della SMA5 e SMA10 e il crossover con VWAP nella stessa candela
        if sma1 > sma2 and self.ma1[-2] < self.ma2[-2]  and self.data.Open[-1] <  vwap and self.data.Close[-1] > vwap:
            stop_loss = self.data.Low[-1] - 0.15
            take_profit = self.data.Close[-1] + 0.30
            self.buy(sl=stop_loss, tp=take_profit)

        # Verifica il crossunder della SMA5 e SMA10 e il crossunder con VWAP nella stessa candela
        elif sma1 < sma2 and self.ma1[-2] > self.ma2[-2]  and self.data.Open[-1] >  vwap and self.data.Close[-1] < vwap:
            stop_loss = self.data.High[-1] + 0.15
            take_profit = self.data.Close[-1] - 0.30
            self.sell(sl=stop_loss, tp=take_profit)


def get_vwap_with_deviation(arr):
    """
    Get the last 5 daily VWAP values and their changes (differences).
    """
    price_volume = arr['Close'] * arr['Volume']

    # Calcola il VWAP cumulativo
    cumulative_price_volume = price_volume.cumsum()
    cumulative_volume = arr['Volume'].cumsum()
    vwap = cumulative_price_volume / cumulative_volume

    return vwap  # Restituisce l'array dei valori VWAP


def get_daily_vwap(df):
    """
    Calcola il VWAP giornaliero per ogni giorno nel DataFrame e lo restituisce in un DataFrame resettato ogni giorno.
    """
    df.index = pd.to_datetime(df.index, utc=True)
    # Trasforma l'indice del DataFrame in una data
    df['Date'] = df.index.date

    # Raggruppa i dati per data e calcola il VWAP per ogni giorno
    df['Daily_VWAP'] = df.groupby('Date').apply(
        lambda x: (x['Close'] * x['Volume']).cumsum() / x['Volume'].cumsum()).reset_index(level=0, drop=True)

    return df

def sma_cross_trading(index = "SP500"):
    global df
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index}  10 min sma crossing stock")

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
                    df_with_daily_vwap = get_daily_vwap(df)

                    # Esegui il backtesting
                    bt = Backtest(df_with_daily_vwap, HOLCStrategy, cash=10000, commission=.002,
                                exclusive_orders = True)
                    stats = bt.run()

                    total_trades = stats['_trades'].shape[0]
                    win_rate = stats['Win Rate [%]']

                    # Controlla se il stock soddisfa i criteri
                    if total_trades > 1 and win_rate > 5:
                        # Salva il grafico in una variabile
                        fig = bt.plot()
                        sr_support = SupportResistanceFinder(data=df)
                        list_sr = sr_support.find_levels()
                        report.add_content(f"stock = {item}")
                        # report.add_content(f"Optimal High_vwap_diff for {item}: {best_high_vwap_diff}")
                        report.add_content(f"Corresponding Win Rate: {win_rate}%")
                        report.add_content(f"total trade = {total_trades}\n")


                        # Aggiungi il nome dello stock come titolo del grafico
                        print(f'Performance del Backtest per {item} (Win Rate: {win_rate}%)')

                except FileNotFoundError:
                # Gestisci l'errore se il file non viene trovato
                    print(f"File non trovato per {item}")
                except Exception as e:
                # Gestisci altri errori generici
                    print(f"Errore durante l'elaborazione di {item}: {e}")
        file_report = report.save_report(filename=f"{index}_sma_cross_stock")
        return file_report

# Preparazione per il backtesting
if __name__ == "__main__":
    # sma_cross_trading(index="Nasdaq")
    # sma_cross_trading(index="Russel")
    sma_cross_trading(index="SP500")

