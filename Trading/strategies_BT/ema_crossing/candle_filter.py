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

class HOLCStrategy_Candle(Strategy):
    last_trade_date = None
    def init(self):
        super().init()
        price = self.data.Close
        self.ema1 = self.I(EMA, price, 9)
        self.ema2 = self.I(EMA, price, 21)


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

    def get_trade_results(self):
        return self.trade_results