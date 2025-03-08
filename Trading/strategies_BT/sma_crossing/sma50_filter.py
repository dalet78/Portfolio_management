from backtesting import Backtest, Strategy
from backtesting.test import SMA
from datetime import time

# Strategy Parameters
ENTRY_START_TIME = time(14, 30)
ENTRY_END_TIME = time(14, 50)
EXIT_TIME = time(20, 50)
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SMA_TREND_PERIOD = 50  # Aggiunta della SMA50 per filtro trend
SL_PERCENT = 0.007
TP_PERCENT = 0.014

class HOLCStrategy_SMA50(Strategy):
    last_trade_date = None
    trade_results = []  # Lista per registrare i risultati dei trade (+1 successo, -1 fallimento)

    def init(self):
        super().init()
        price = self.data.Close
        self.ma1 = self.I(SMA, price, SMA_SHORT_PERIOD)   # SMA5
        self.ma2 = self.I(SMA, price, SMA_LONG_PERIOD)    # SMA20
        self.ma50 = self.I(SMA, price, SMA_TREND_PERIOD)  # SMA50 (nuovo filtro trend)

    def next(self):
        if len(self.data.Close) < 3:  # Assicura che ci siano abbastanza dati
            return

        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        # SMA sulla candela di crossover
        sma1 = self.ma1[-2]  # SMA5 sulla candela di crossover
        sma2 = self.ma2[-2]  # SMA20 sulla candela di crossover
        sma50 = self.ma50[-2]  # SMA50 sulla candela di crossover

        # Prezzo di apertura della candela successiva al crossover
        next_candle_open = self.data.Open[-1]  # ENTRY PRICE all'apertura della candela successiva

        if self.position:
            last_trade = self.trades[-1] if self.trades else None
            if last_trade and last_trade.pl is not None:  # Controllo corretto per trade chiuso
                profit = last_trade.pl
                self.trade_results.append(1 if profit > 0 else -1)
                self.last_trade_date = None  # Resetta la data dell'ultimo trade

        elif ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and (
                self.last_trade_date is None or self.last_trade_date != current_date):

            # **Bullish Crossover**: SMA5 > SMA20 e avviene SOPRA la SMA50
            if sma1 > sma2 and self.ma1[-3] <= self.ma2[-3] and self.data.Close[-1] > sma50:
                entry_price = next_candle_open  # ENTRY all'apertura della candela successiva
                stop_loss = entry_price - (SL_PERCENT * entry_price)
                take_profit = entry_price + (TP_PERCENT * entry_price)
                self.buy(limit=entry_price, sl=stop_loss, tp=take_profit)

            # **Bearish Crossover**: SMA5 < SMA20 e avviene SOTTO la SMA50
            elif sma1 < sma2 and self.ma1[-3] >= self.ma2[-3] and self.data.Close[-1] < sma50:
                entry_price = next_candle_open  # ENTRY all'apertura della candela successiva
                stop_loss = entry_price + (SL_PERCENT * entry_price)
                take_profit = entry_price - (TP_PERCENT * entry_price)
                self.sell(limit=entry_price, sl=stop_loss, tp=take_profit)

            self.last_trade_date = current_date

    def get_trade_results(self):
        return self.trade_results
