from datetime import time
import pandas as pd
import numpy as np
from backtesting import Strategy

# Strategy Parameters
ENTRY_START_TIME = time(14, 30)
ENTRY_END_TIME   = time(15, 0)
EXIT_TIME        = time(19, 50)
SL_PERCENT = 0.007
TP_PERCENT = 0.014

class NR7Strategy(Strategy):
    last_trade_date = None
    nr7_high = None
    nr7_low = None

    def init(self):
        super().init()
        self.range7 = self.I(self.compute_nr7_range)

    def compute_nr7_range(self):
        high = self.data.High
        low = self.data.Low
        ranges = pd.Series(high - low)
        is_nr7 = ranges.rolling(7).apply(lambda x: x[-1] == min(x), raw=True)
        return is_nr7.fillna(0).astype(bool).values

    def next(self):
        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        # Chiudi la posizione alla fine
        if self.position and current_time >= EXIT_TIME:
            self.position.close()
            self.last_trade_date = None

        elif ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and (
                self.last_trade_date is None or self.last_trade_date != current_date):

            # Se la candela precedente era NR7, salviamo high/low
            if self.range7[-2]:
                self.nr7_high = self.data.High[-2]
                self.nr7_low  = self.data.Low[-2]

            # Se abbiamo un NR7 precedente, controlliamo breakout
            if self.nr7_high and self.nr7_low:
                close = self.data.Close[-1]
                open_ = self.data.Open[-1]
                high = self.data.High[-1]
                low = self.data.Low[-1]

                # 🔹 Filtro 1: range normale
                daily_range = high - low
                recent_ranges = self.data.High - self.data.Low
                if len(recent_ranges) < 10:
                    return  # non abbastanza dati
                avg_range = pd.Series(recent_ranges[-10:]).mean()
                if not (0.8 * avg_range < daily_range < 1.2 * avg_range):
                    return

                # 🔹 Filtro 2: breakout con corpo > 50% del range
                body = abs(close - open_)
                if body < 0.5 * daily_range:
                    return

                if close > self.nr7_high:
                    sl = close - SL_PERCENT * close
                    tp = close + TP_PERCENT * close
                    self.buy(sl=sl, tp=tp)
                    self.last_trade_date = current_date
                    self.nr7_high = None  # reset

                elif close < self.nr7_low:
                    sl = close + SL_PERCENT * close
                    tp = close - TP_PERCENT * close
                    self.sell(sl=sl, tp=tp)
                    self.last_trade_date = current_date
                    self.nr7_low = None  # reset
