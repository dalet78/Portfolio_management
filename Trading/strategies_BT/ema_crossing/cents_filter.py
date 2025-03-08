from backtesting import Backtest, Strategy
from backtesting.test import SMA, EMA
from datetime import time

# Strategy Parameters
ENTRY_START_TIME = time(14, 30)
ENTRY_END_TIME = time(14, 50)
EXIT_TIME = time(20, 50)
EMA_SHORT_PERIOD = 9
EMA_LONG_PERIOD = 21
SL_PERCENT = 0.007
TP_PERCENT = 0.014


class HOLCStrategy_cents(Strategy):
    last_trade_date = None

    def init(self):
        super().init()
        price = self.data.Close
        self.ema1 = self.I(EMA, price, EMA_SHORT_PERIOD)
        self.ema2 = self.I(EMA, price, EMA_LONG_PERIOD)

    def next(self):
        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        ema1 = self.ema1[-1]
        ema2 = self.ema2[-1]
        prev_ema1 = self.ema1[-2]
        prev_ema2 = self.ema2[-2]
        candle_close = self.data.Close[-1]
        prev_candle_close = self.data.Close[-2]

        # Close position at EXIT_TIME
        if self.position and current_time >= EXIT_TIME:
            self.position.close()
            self.last_trade_date = None

        # Entry logic within allowed trading time
        elif ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and (
                self.last_trade_date is None or self.last_trade_date != current_date):

            if ema1 > ema2 and prev_ema1 <= prev_ema2:  # Bullish crossover
                entry_price = prev_candle_close + 0.02
                stop_loss = entry_price - (SL_PERCENT * entry_price)
                take_profit = entry_price + (TP_PERCENT * entry_price)
                self.buy(limit=entry_price, sl=stop_loss, tp=take_profit)

            elif ema1 < ema2 and prev_ema1 >= prev_ema2:  # Bearish crossover
                entry_price = prev_candle_close - 0.02
                stop_loss = entry_price + (SL_PERCENT * entry_price)
                take_profit = entry_price - (TP_PERCENT * entry_price)
                self.sell(limit=entry_price, sl=stop_loss, tp=take_profit)

            self.last_trade_date = current_date

    def get_trade_results(self):
        return self.trade_results