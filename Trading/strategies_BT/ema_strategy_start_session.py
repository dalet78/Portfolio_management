import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, EMA
import json
from libs.filtered_stock import return_filtred_list
from datetime import time
import matplotlib.pyplot as plt
from Reports.report_builder import ReportGenerator
from support.data_preparation import DataRefactory
# from Trading.methodology.PriceAction.sma_vwap_sr_support import SupportResistanceFinder

# Strategy Parameters
ENTRY_START_TIME = time(14, 30)
ENTRY_END_TIME = time(14, 50)
EXIT_TIME = time(20, 50)
EMA_SHORT_PERIOD = 9
EMA_LONG_PERIOD = 21
SL_PERCENT = 0.007
TP_PERCENT = 0.014

class HOLCStrategy(Strategy):
    last_trade_date = None
    def init(self):
        super().init()
        price = self.data.Close
        self.ema1 = self.I(EMA, price, 9)
        self.ema2 = self.I(EMA, price, 21)
        # print(df.head())

    def next(self):
        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        ema1 = self.ema1[-1]
        ema2 = self.ema2[-1]
        candle_direction = "bullish" if self.data.Close[-1] > self.data.Open[-1] else "bearish"

        if self.position and current_time >= EXIT_TIME:
            self.position.close()
            self.last_trade_date = None

        elif ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and (
                self.last_trade_date is None or self.last_trade_date != current_date):

            # Verifica il crossover della SMA5 e SMA10
            if ema1 > ema2 and self.ema1[-2] <= self.ema2[-2] and candle_direction == "bullish":
                stop_loss = self.data.Close[-1] - (SL_PERCENT * self.data.Close[-1])
                take_profit = self.data.Close[-1] + (TP_PERCENT * self.data.Close[-1])
                self.buy(sl=stop_loss, tp=take_profit)

            # Verifica il crossunder della SMA5 e SMA10
            elif ema1 < ema2 and self.ema1[-2] >= self.ema2[-2] and candle_direction == "bearish":
                stop_loss = self.data.Close[-1] + (SL_PERCENT * self.data.Close[-1])
                take_profit = self.data.Close[-1] - (TP_PERCENT * self.data.Close[-1])
                self.sell(sl=stop_loss, tp=take_profit)

            self.last_trade_date = current_date


def ema_cross_trading(index = "SP500"):
    global df
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index}  10 min EMA9 - EMA21 crossing stock")
    report.add_content(f"Strategy Description:\n")
    report.add_content(f"1. Timeframe: 5-minute candles\n")
    report.add_content(f"2. Entry window: {ENTRY_START_TIME} - {ENTRY_END_TIME}\n")
    report.add_content(f"3. Exit time: {EXIT_TIME}\n")
    report.add_content(
        f"4. Buy Condition: EMA{EMA_SHORT_PERIOD} crosses above EMA{EMA_LONG_PERIOD} with a bullish candle\n")
    report.add_content(
        f"5. Sell Condition: EMA{EMA_SHORT_PERIOD} crosses below EMA{EMA_LONG_PERIOD} with a bearish candle\n")
    report.add_content(f"6. Take Profit: {TP_PERCENT * 100}% - Stop Loss: {SL_PERCENT * 100}%\n")

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
                df = DataRefactory.prepare_min_csv(filepath=data_filepath)

                # Esegui il backtesting
                bt = Backtest(df, HOLCStrategy, cash=10000, exclusive_orders = True)
                stats = bt.run()

                print(stats)
                total_trades = stats['_trades'].shape[0]
                win_rate = stats['Win Rate [%]']
                sharpe_ratio = stats['Sharpe Ratio']
                max_drawdown = stats['Max. Drawdown [%]']
                total_return = stats['Return [%]']
                cagr = stats['CAGR [%]']
                # commission = stats['Commissions [$]']

                # Controlla se il stock soddisfa i criteri
                if total_trades > 3 and win_rate > 40:
                    # Salva il grafico in una variabile
                    # fig = bt.plot()
                    # sr_support = SupportResistanceFinder(data=df)
                    # list_sr = sr_support.find_levels()
                    report.add_content(f"Stock = {item}")
                    report.add_content(f"Corresponding Win Rate: {win_rate}%")
                    report.add_content(f"Total Trades = {total_trades}")
                    report.add_content(f"Sharpe Ratio = {sharpe_ratio}")
                    report.add_content(f"Max Drawdown = {max_drawdown}%")
                    report.add_content(f"Total Return = {total_return}%")
                    report.add_content(f"CAGR = {cagr}%\n")
                    # report.add_content(f"Commission = {commission}$\n")

                    # Aggiungi il nome dello stock come titolo del grafico
                    print(f'Performance del Backtest per {item} (Win Rate: {win_rate}%)')

            except FileNotFoundError:
            # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
            # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")
    file_report = report.save_report(filename=f"{index}_ema_cross_stock")
    return file_report

# Preparazione per il backtesting
if __name__ == "__main__":
    ema_cross_trading(index="ALL")


