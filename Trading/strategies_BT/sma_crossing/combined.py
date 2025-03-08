from backtesting import Strategy
from backtesting.test import SMA
from datetime import time

# Strategy Parameters
ENTRY_START_TIME = time(14, 30)
ENTRY_END_TIME = time(14, 50)
EXIT_TIME = time(20, 50)
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SMA_TREND_PERIOD = 50  # Per filtro trend
SL_PERCENT = 0.007
TP_PERCENT = 0.014

class HOLCStrategy_Combined(Strategy):
    last_trade_date = None

    def init(self):
        """Inizializza gli indicatori della strategia"""
        super().init()
        price = self.data.Close
        self.ma1 = self.I(SMA, price, SMA_SHORT_PERIOD)   # SMA5
        self.ma2 = self.I(SMA, price, SMA_LONG_PERIOD)    # SMA20
        self.ma50 = self.I(SMA, price, SMA_TREND_PERIOD)  # SMA50 per il filtro trend

    def next(self):
        """Logica della strategia"""
        if len(self.data.Close) < 3:
            return

        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        # Prezzi della candela di crossover e della successiva
        prev_candle_close = self.data.Close[-2]  # Chiusura della candela di crossover
        prev_candle_open = self.data.Open[-2]    # Apertura della candela di crossover
        next_candle_open = self.data.Open[-1]    # Apertura della candela successiva (ENTRY PRICE)

        # SMA attuali
        sma1 = self.ma1[-2]  # SMA5 sulla candela di crossover
        sma2 = self.ma2[-2]  # SMA20 sulla candela di crossover
        sma50 = self.ma50[-2]  # SMA50 sulla candela di crossover

        # Direzione della candela
        candle_direction = "bullish" if prev_candle_close > prev_candle_open else "bearish"

        # **Filtro HOLCStrategy_Candle**: la candela deve confermare il trend
        candle_filter_passed = (candle_direction == "bullish" and sma1 > sma2) or \
                               (candle_direction == "bearish" and sma1 < sma2)

        # **Filtro HOLCStrategy_SMA50**: crossover deve avvenire sopra/sotto la SMA50
        sma50_filter_passed = (sma1 > sma50 and sma1 > sma2) or (sma1 < sma50 and sma1 < sma2)

        # **Conferma trade**: almeno uno dei due filtri deve essere attivo
        trade_confirmed = candle_filter_passed or sma50_filter_passed

        # **Verifica orari di ingresso**
        if not (ENTRY_START_TIME <= current_time <= ENTRY_END_TIME):
            return

        if trade_confirmed:
            if self.position:
                last_trade = self.trades[-1] if self.trades else None
                if last_trade and last_trade.pl is not None:
                    self.last_trade_date = None  # Resetta la data dell'ultimo trade

            elif self.last_trade_date is None or self.last_trade_date != current_date:

                # **Bullish Crossover**: SMA5 > SMA20 e almeno uno dei filtri è attivo
                if sma1 > sma2 and self.ma1[-3] <= self.ma2[-3]:
                    entry_price = prev_candle_close + 0.02  # ENTRY a 2 cent sopra la chiusura della candela di cross
                    stop_loss = entry_price - (SL_PERCENT * entry_price)
                    take_profit = entry_price + (TP_PERCENT * entry_price)
                    self.buy(limit=entry_price, sl=stop_loss, tp=take_profit)

                # **Bearish Crossover**: SMA5 < SMA20 e almeno uno dei filtri è attivo
                elif sma1 < sma2 and self.ma1[-3] >= self.ma2[-3]:
                    entry_price = prev_candle_close - 0.02  # ENTRY a 2 cent sotto la chiusura della candela di cross
                    stop_loss = entry_price + (SL_PERCENT * entry_price)
                    take_profit = entry_price - (TP_PERCENT * entry_price)
                    self.sell(limit=entry_price, sl=stop_loss, tp=take_profit)

                self.last_trade_date = current_date
