from backtesting import Strategy
from datetime import time
import talib

# Costanti
ENTRY_START_TIME = time(16, 30)
ENTRY_END_TIME = time(18, 0)
EXIT_TIME = time(19, 50)
ENTRY_THRESHOLD = 0.014  # 1.4%
SL_PERCENT = 0.007       # 0.7%

class VWAPReversalStrategy(Strategy):
    last_trade_date = None

    def init(self):
        super().init()
        self.vwap = self.data.vwap

    def next(self):
        price = self.data.Close[-1]
        high = self.data.High[-1]
        low = self.data.Low[-1]
        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()
        vwap_now = self.vwap[-1]

        # Chiudi forzatamente la posizione alle EXIT_TIME
        if self.position and current_time >= EXIT_TIME:
            self.position.close()
            # print(f"⏹️ Posizione chiusa forzatamente alle {EXIT_TIME}")

        # Apri una nuova posizione solo se non ce n'è una e non hai già tradato oggi
        elif (ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and
              not self.position and
              (self.last_trade_date is None or self.last_trade_date != current_date)):

            # Condizione LONG
            if (vwap_now - low) / vwap_now >= ENTRY_THRESHOLD:
                stop_loss = low - (SL_PERCENT * low)
                take_profit = vwap_now
                if take_profit > price and stop_loss < price:
                    self.buy(sl=stop_loss, tp=take_profit)
                    self.last_trade_date = current_date  # <-- Qui salvi la data del trade
                    # print(f"✅ LONG aperto | Prezzo: {price}, SL: {stop_loss}, TP: {take_profit}")
                else:
                    print(f"❌ LONG non valido | Prezzo: {price}, SL: {stop_loss}, TP: {take_profit}")

            # Condizione SHORT
            elif (high - vwap_now) / vwap_now >= ENTRY_THRESHOLD:
                stop_loss = high + (SL_PERCENT * high)
                take_profit = vwap_now
                if take_profit < price and stop_loss > price:
                    self.sell(sl=stop_loss, tp=take_profit)
                    self.last_trade_date = current_date  # <-- Anche qui
                    # print(f"✅ SHORT aperto | Prezzo: {price}, SL: {stop_loss}, TP: {take_profit}")
                else:
                    print(f"❌ SHORT non valido | Prezzo: {price}, SL: {stop_loss}, TP: {take_profit}")


def add_vwap(df):
    """Aggiunge la colonna VWAP al DataFrame"""
    df = df.copy()
    df['price_volume'] = df['Close'] * df['Volume']
    df['cum_pv'] = df.groupby(df.index.normalize())['price_volume'].cumsum()
    df['cum_vol'] = df.groupby(df.index.normalize())['Volume'].cumsum()
    df['vwap'] = df['cum_pv'] / df['cum_vol']
    return df