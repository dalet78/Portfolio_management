from backtesting import Backtest, Strategy
from backtesting.test import SMA
from datetime import time


# Strategy Parameters
ENTRY_START_TIME = time(14, 30)
ENTRY_END_TIME = time(14, 50)
EXIT_TIME = time(20, 50)
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SL_PERCENT = 0.007
TP_PERCENT = 0.014


class HOLCStrategy_cents(Strategy):
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