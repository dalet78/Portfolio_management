from backtesting import Backtest, Strategy
from backtesting.test import SMA
from datetime import time

# === PARAMETRI STRATEGIA ===
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SMA_TREND_PERIOD = 50

SL_PERCENT = 0.007  # 0.5%
TP_PERCENT = 0.014   # 1%

# Orari di interesse per il cross (UTC)
ENTRY_CROSS_TIMES = {time(13, 35), time(13, 40)}
MARKET_OPEN_TIME = time(13, 30)

class HOLCStrategy_SMA50(Strategy):
    last_trade_date = None
    trade_results = []
    dubious_trades = []  # Per registrare i trade potenzialmente "dubbi"

    def init(self):
        super().init()
        price = self.data.Close
        self.ma1 = self.I(SMA, price, SMA_SHORT_PERIOD)   # SMA5
        self.ma2 = self.I(SMA, price, SMA_LONG_PERIOD)    # SMA20
        self.ma50 = self.I(SMA, price, SMA_TREND_PERIOD)  # SMA50 (trend filter)

        # Controllo che i dati inizino a mercato aperto (14:30 UTC)
        if self.data.index[0].time() != MARKET_OPEN_TIME:
            print(f"⚠️ ATTENZIONE: i dati iniziano a {self.data.index[0].time()}, non alle {MARKET_OPEN_TIME}.")
            # In produzione potresti anche lanciare un'eccezione.

    def next(self):
        if len(self.data.Close) < 3:
            return  # Non abbastanza dati per valutare cross

        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        sma1_now = self.ma1[-2]  # Due candele indietro perché il cross si misura sulla chiusa precedente
        sma2_now = self.ma2[-2]
        sma50_now = self.ma50[-2]

        next_candle_open = self.data.Open[-1]

        if self.position:
            last_trade = self.trades[-1] if self.trades else None
            if last_trade and last_trade.pl is not None:
                # Controllo se il trade è stato aperto e chiuso nella stessa candela
                if last_trade.entry_bar == last_trade.exit_bar:
                    self.dubious_trades.append({
                        "entry_time": last_trade.entry_time,
                        "exit_time": last_trade.exit_time,
                        "pnl": last_trade.pl
                    })

                profit = last_trade.pl
                self.trade_results.append(1 if profit > 0 else -1)
                self.last_trade_date = None

        # Se siamo all'interno delle candele di interesse e non abbiamo ancora tradato oggi
        elif current_time in ENTRY_CROSS_TIMES and (
                self.last_trade_date is None or self.last_trade_date != current_date):

            # Condizioni di ingresso LONG
            if sma1_now > sma2_now and self.ma1[-3] <= self.ma2[-3] and self.data.Close[-1] > sma50_now:
                entry_price = next_candle_open
                stop_loss = entry_price - (SL_PERCENT * entry_price)
                take_profit = entry_price + (TP_PERCENT * entry_price)
                self.buy(limit=entry_price, sl=stop_loss, tp=take_profit)

            # Condizioni di ingresso SHORT
            elif sma1_now < sma2_now and self.ma1[-3] >= self.ma2[-3] and self.data.Close[-1] < sma50_now:
                entry_price = next_candle_open
                stop_loss = entry_price + (SL_PERCENT * entry_price)
                take_profit = entry_price - (TP_PERCENT * entry_price)
                self.sell(limit=entry_price, sl=stop_loss, tp=take_profit)

            self.last_trade_date = current_date

    def get_trade_results(self):
        return self.trade_results

    def get_dubious_trades(self):
        return self.dubious_trades
