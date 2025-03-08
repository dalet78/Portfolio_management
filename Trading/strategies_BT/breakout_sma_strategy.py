import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.test import SMA
import json
from libs.filtered_stock import return_filtred_list
from datetime import time
from Reports.report_builder import ReportGenerator
from support.data_preparation import DataRefactory

# Strategy Parameters
RANGE_START_TIME = time(14, 30)
RANGE_END_TIME = time(14, 45)
ENTRY_START_TIME = time(14, 45)
ENTRY_STOP_TIME = time(15, 00)
EXIT_TIME = time(20, 50)
SMA20_PERIOD = 20
SMA50_PERIOD = 50
ATR_PERIOD = 20
SL_PERCENT = 0.005
TP_PERCENT = 0.01
BREAKOUT_MULTIPLIER = 1.5

class ORB_SMA20_Strategy(Strategy):
    last_trade_date = None

    def init(self):
        super().init()
        price = self.data.Close
        self.sma20 = self.I(SMA, price, SMA20_PERIOD)
        self.sma50 = self.I(SMA, price, SMA50_PERIOD)
        self.atr = self.I(lambda x: pd.Series(x).rolling(ATR_PERIOD).std(), price)  # Approximate ATR
        self.orb_high = None
        self.orb_low = None
        self.orb_set = False

    def next(self):
        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        # Calculate ORB range
        if not self.orb_set and RANGE_START_TIME <= current_time <= RANGE_END_TIME:
            self.orb_high = max(self.data.High[-3:])
            self.orb_low = min(self.data.Low[-3:])
            self.orb_set = True

        # Close position at the end of the day
        if self.position and current_time >= EXIT_TIME:
            self.position.close()
            self.orb_set = False
            self.last_trade_date = None

        # Trade entry logic
        elif self.orb_set and ENTRY_START_TIME <= current_time <= ENTRY_STOP_TIME and not self.position:
            if self.last_trade_date == current_date:
                return

            price = self.data.Close[-1]
            sma20 = self.sma20[-1]
            sma50 = self.sma50[-1]
            atr = self.atr[-1]

            # Strong breakout condition
            strong_breakout = (self.orb_high - self.orb_low) > (BREAKOUT_MULTIPLIER * atr)

            if price > self.orb_high and price > sma20 and strong_breakout:
                if sma20 > sma50:
                    stop_loss = price * (1 - SL_PERCENT)
                    take_profit = price * (1 + TP_PERCENT)
                    self.buy(sl=stop_loss, tp=take_profit)
                    self.last_trade_date = current_date

            elif price < self.orb_low and price < sma20 and strong_breakout:
                if sma20 < sma50:
                    stop_loss = price * (1 + SL_PERCENT)
                    take_profit = price * (1 - TP_PERCENT)
                    self.sell(sl=stop_loss, tp=take_profit)
                    self.last_trade_date = current_date

def orb_sma_trading(index="SP500"):
    global df
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} ORB + SMA20 Strategy")
    report.add_content(f"Breakout strategy with SMA20 filter\n")
    report.add_content(f"TP={TP_PERCENT*100}% - SL={SL_PERCENT*100}% - Range = First 3 candles\n")
    report.add_content("\nStrategy Rules:\n")
    report.add_content(f"1. ORB Range is calculated from {RANGE_START_TIME} to {RANGE_END_TIME} using the high and low of the first 3 candles.\n")
    report.add_content(f"2. Entry window: {ENTRY_START_TIME} to {ENTRY_STOP_TIME}, provided that the strong breakout condition is met.\n")
    report.add_content("3. RSI filter: No trade if RSI < 30 or RSI > 70.\n")
    report.add_content(f"4. Trade confirmation: SMA{SMA20_PERIOD} must be above SMA{SMA50_PERIOD} for long trades, and below for short trades.\n")
    report.add_content(f"5. Stop Loss: {SL_PERCENT*100}%, Take Profit: {TP_PERCENT*100}%.\n")
    report.add_content(f"6. All positions are closed at {EXIT_TIME}.\n")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)
        tickers_list = return_filtred_list(index=index)

        if not tickers_list:
            print("Nessun ticker soddisfa i criteri di selezione.")
        else:
            for item in tickers_list:
                print(f'Analyze stock = {item}')
                try:
                    data_filepath = f"{source_directory}/Data/{index}/5min/{item}_historical_data.csv"
                    df = DataRefactory.prepare_5m_csv(filepath=data_filepath)

                    bt = Backtest(df, ORB_SMA20_Strategy, cash=10000, commission=.002, exclusive_orders=True)
                    stats = bt.run()

                    total_trades = stats['_trades'].shape[0]
                    win_rate = stats['Win Rate [%]']

                    if total_trades > 3 and win_rate > 50:
                        fig = bt.plot()
                        report.add_content(f"Stock = {item}")
                        report.add_content(f"Win Rate: {win_rate}%")
                        report.add_content(f"Total trades = {total_trades}\n")

                        print(f'Performance del Backtest per {item} (Win Rate: {win_rate}%)')

                except FileNotFoundError:
                    print(f"File non trovato per {item}")
                except Exception as e:
                    print(f"Errore durante l'elaborazione di {item}: {e}")

        file_report = report.save_report(filename=f"{index}_orb_sma20_stock")
        return file_report

if __name__ == "__main__":
    orb_sma_trading(index="ALL")
