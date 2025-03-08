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
GAP_THRESHOLD = 0.01  # 1% di gap

class HOLCStrategy_Gap(Strategy):
    last_trade_date = None
    trade_results = []  # Lista per registrare i risultati dei trade (+1 successo, -1 fallimento)
    session_invalid = False  # Flag per marcare sessioni non valide

    def init(self):
        super().init()
        price = self.data.Close
        self.ma1 = self.I(SMA, price, SMA_SHORT_PERIOD)
        self.ma2 = self.I(SMA, price, SMA_LONG_PERIOD)

    def next(self):
        if len(self.data.Close) < 3:  # Assicura che ci siano abbastanza dati
            return

        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        # Prezzi della sessione attuale
        candle_close = self.data.Close[-2]  # Chiusura della candela di crossover
        candle_open = self.data.Open[-2]  # Apertura della candela di crossover
        next_candle_open = self.data.Open[-1]  # Apertura della candela successiva (ENTRY PRICE)

        # Calcola il gap rispetto alla sessione precedente
        if current_time == ENTRY_START_TIME:  # Prima candela della sessione
            previous_session_close = self.data.Close[-3]  # Chiusura dell'ultima candela della sessione precedente
            gap_percent = abs((candle_close - previous_session_close) / previous_session_close)

            # Se il gap è maggiore dell'1%, la sessione è invalida
            self.session_invalid = gap_percent > GAP_THRESHOLD

        # Se la sessione è invalida, non entriamo
        if self.session_invalid:
            return

        # SMA sulla candela di crossover
        sma1 = self.ma1[-2]  # SMA5 sulla candela di crossover
        sma2 = self.ma2[-2]  # SMA20 sulla candela di crossover

        if self.position:
            last_trade = self.trades[-1] if self.trades else None
            if last_trade and last_trade.pl is not None:  # Controllo corretto per trade chiuso
                profit = last_trade.pl
                self.trade_results.append(1 if profit > 0 else -1)
                self.last_trade_date = None  # Resetta la data dell'ultimo trade

        elif ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and (
                self.last_trade_date is None or self.last_trade_date != current_date):

            # **Bullish Crossover**: SMA5 > SMA20
            if sma1 > sma2 and self.ma1[-3] <= self.ma2[-3]:
                entry_price = next_candle_open  # ENTRY all'apertura della candela successiva
                stop_loss = entry_price - (SL_PERCENT * entry_price)
                take_profit = entry_price + (TP_PERCENT * entry_price)
                self.buy(limit=entry_price, sl=stop_loss, tp=take_profit)

            # **Bearish Crossover**: SMA5 < SMA20
            elif sma1 < sma2 and self.ma1[-3] >= self.ma2[-3]:
                entry_price = next_candle_open  # ENTRY all'apertura della candela successiva
                stop_loss = entry_price + (SL_PERCENT * entry_price)
                take_profit = entry_price - (TP_PERCENT * entry_price)
                self.sell(limit=entry_price, sl=stop_loss, tp=take_profit)

            self.last_trade_date = current_date

    def get_trade_results(self):
        return self.trade_results
