from backtesting import Backtest, Strategy
from backtesting.test import SMA, EMA
from datetime import time

# Strategy Parameters
ENTRY_START_TIME = time(14, 30)
ENTRY_END_TIME = time(14, 50)
EXIT_TIME = time(20, 50)
EMA_SHORT_PERIOD = 9
EMA_LONG_PERIOD = 21
EMA_TREND_PERIOD = 50  # EMA50 come filtro di trend
SL_PERCENT = 0.007
TP_PERCENT = 0.014


class HOLCStrategy_Ema50(Strategy):
    last_trade_date = None

    def init(self):
        super().init()
        price = self.data.Close
        self.ema1 = self.I(EMA, price, EMA_SHORT_PERIOD)  # EMA9
        self.ema2 = self.I(EMA, price, EMA_LONG_PERIOD)  # EMA21
        self.ema50 = self.I(EMA, price, EMA_TREND_PERIOD)  # EMA50 come filtro di trend

    def next(self):
        if len(self.data.Close) < 3:  # Assicura che ci siano abbastanza dati
            return

        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        ema1 = self.ema1[-2]  # EMA9 sulla candela di crossover
        ema2 = self.ema2[-2]  # EMA21 sulla candela di crossover
        ema50 = self.ema50[-2]  # EMA50 sulla candela di crossover

        next_candle_open = self.data.Open[-1]  # ENTRY PRICE all'apertura della candela successiva

        # Close position at EXIT_TIME
        if self.position and current_time >= EXIT_TIME:
            self.position.close()
            self.last_trade_date = None

        elif ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and (
                self.last_trade_date is None or self.last_trade_date != current_date):

            # **Bullish Crossover**: EMA9 > EMA21 e avviene SOPRA la EMA50
            if ema1 > ema2 and self.ema1[-3] <= self.ema2[-3] and self.data.Close[-1] > ema50:
                entry_price = next_candle_open  # ENTRY all'apertura della candela successiva
                stop_loss = entry_price - (SL_PERCENT * entry_price)
                take_profit = entry_price + (TP_PERCENT * entry_price)
                self.buy(limit=entry_price, sl=stop_loss, tp=take_profit)

            # **Bearish Crossover**: EMA9 < EMA21 e avviene SOTTO la EMA50
            elif ema1 < ema2 and self.ema1[-3] >= self.ema2[-3] and self.data.Close[-1] < ema50:
                entry_price = next_candle_open  # ENTRY all'apertura della candela successiva
                stop_loss = entry_price + (SL_PERCENT * entry_price)
                take_profit = entry_price - (TP_PERCENT * entry_price)
                self.sell(limit=entry_price, sl=stop_loss, tp=take_profit)

            self.last_trade_date = current_date

    def get_trade_results(self):
        return self.trade_results