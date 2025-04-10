import pandas as pd
import numpy as np
import os
import csv
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
import json
from libs.filtered_stock import return_filtred_list
from datetime import time
import matplotlib.pyplot as plt
from Reports.report_builder import ReportGenerator
from support.data_preparation import DataRefactory


# Strategy Parameters
ENTRY_START_TIME = time(14, 30)
ENTRY_END_TIME = time(14, 50)
EXIT_TIME = time(20, 50)
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SL_PERCENT = 0.007
TP_PERCENT = 0.014


class HOLCStrategy(Strategy):
    last_trade_date = None
    trade_results = []  # Lista per registrare i risultati dei trade (+1 successo, -1 fallimento)

    def init(self):
        super().init()
        price = self.data.Close
        self.ma1 = self.I(SMA, price, SMA_SHORT_PERIOD)
        self.ma2 = self.I(SMA, price, SMA_LONG_PERIOD)

    def next(self):
        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        sma1 = self.ma1[-1]
        sma2 = self.ma2[-1]
        candle_close = self.data.Close[-1]
        candle_open = self.data.Open[-1]
        candle_high = self.data.High[-1]
        candle_low = self.data.Low[-1]
        prev_candle_close = self.data.Close[-2]

        candle_direction = "bullish" if candle_close > candle_open else "bearish"

        if self.position:
            last_trade = self.trades[-1] if self.trades else None
            if last_trade and last_trade.pl is not None:  # Controllo corretto per trade chiuso
                profit = last_trade.pl
                self.trade_results.append(1 if profit > 0 else -1)
                self.last_trade_date = None  # Resetta la data dell'ultimo trade

        elif ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and (
                self.last_trade_date is None or self.last_trade_date != current_date):

            if sma1 > sma2 and self.ma1[-2] <= self.ma2[-2]:  # Bullish crossover
                entry_price = prev_candle_close + 0.02
                stop_loss = entry_price - (SL_PERCENT * entry_price)
                take_profit = entry_price + (TP_PERCENT * entry_price)
                self.buy(limit=entry_price, sl=stop_loss, tp=take_profit)

            elif sma1 < sma2 and self.ma1[-2] >= self.ma2[-2]:  # Bearish crossover
                entry_price = prev_candle_close - 0.02
                stop_loss = entry_price + (SL_PERCENT * entry_price)
                take_profit = entry_price - (TP_PERCENT * entry_price)
                self.sell(limit=entry_price, sl=stop_loss, tp=take_profit)

            self.last_trade_date = current_date

    def get_trade_results(self):
        return self.trade_results



def sma_cross_trading(index="SP500"):
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} 15 min SMA Crossing Strategy")
    report.add_content(f"Strategy Description:\n")
    report.add_content(f"1. Timeframe: 5-minute candles\n")
    report.add_content(f"2. Entry window: {ENTRY_START_TIME} - {ENTRY_END_TIME}\n")
    report.add_content(f"3. Exit time: {EXIT_TIME}\n")
    report.add_content(
        f"4. Buy Condition: SMA{SMA_SHORT_PERIOD} crosses above SMA{SMA_LONG_PERIOD} with a bullish candle\n")
    report.add_content(
        f"5. Sell Condition: SMA{SMA_SHORT_PERIOD} crosses below SMA{SMA_LONG_PERIOD} with a bearish candle\n")
    report.add_content(f"6. Take Profit: {TP_PERCENT * 100}% - Stop Loss: {SL_PERCENT * 100}%\n")

    tickers_list = return_filtred_list(index=index)

    csv_filename = f"{source_directory}/Reports/Data/trading_results_{index}.csv"
    csv_exists = os.path.isfile(csv_filename)

    with open(csv_filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Stock"] + [f"Trade_{i + 1}" for i in range(50)])

        if not tickers_list:
            print("Nessun ticker soddisfa i criteri di selezione.")
        else:
            trade_results_dict = {}
            for item in tickers_list:
                print(f'Analyze stock = {item}')
                try:
                    data_filepath = f"{source_directory}/Data/{index}/5min/{item}_historical_data.csv"
                    df = DataRefactory.prepare_min_csv(filepath=data_filepath)

                    bt = Backtest(df, HOLCStrategy, cash=10000, exclusive_orders=True)
                    stats = bt.run()

                    total_trades = stats['_trades'].shape[0]
                    win_rate = stats['Win Rate [%]']
                    sharpe_ratio = stats['Sharpe Ratio']
                    max_drawdown = stats['Max. Drawdown [%]']
                    total_return = stats['Return [%]']
                    cagr = stats['CAGR [%]']

                    if 'ReturnPct' in stats._trades.columns:
                        trade_results = stats._trades['ReturnPct'].tolist()
                    else:
                        trade_results = []

                        # Salvare solo gli stock che hanno trade
                    if trade_results:
                        trade_results_dict[item] = trade_results

                    # Scrive i risultati nel CSV
                    writer.writerow([item] + trade_results)

                    if total_trades > 3 and win_rate > 40:
                        report.add_content(f"Stock = {item}")
                        report.add_content(f"Corresponding Win Rate: {win_rate}%")
                        report.add_content(f"Total Trades = {total_trades}")
                        report.add_content(f"Sharpe Ratio = {sharpe_ratio}")
                        report.add_content(f"Max Drawdown = {max_drawdown}%")
                        report.add_content(f"Total Return = {total_return}%")
                        report.add_content(f"CAGR = {cagr}%\n")

                    print(f'Performance del Backtest per {item} (Win Rate: {win_rate}%)')

                except FileNotFoundError:
                    print(f"File non trovato per {item}")
                except Exception as e:
                    print(f"Errore durante l'elaborazione di {item}: {e}")

    file_report = report.save_report(filename=f"{index}_sma_cross_stock")
    return file_report



if __name__ == "__main__":
    sma_cross_trading(index="ALL")