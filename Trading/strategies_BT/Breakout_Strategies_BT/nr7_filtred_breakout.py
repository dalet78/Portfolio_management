from backtesting import Strategy
import numpy as np
import pandas as pd
from datetime import time

# Parametri della strategia
ENTRY_START_TIME = time(14, 30)
ENTRY_END_TIME   = time(15, 0)
EXIT_TIME        = time(19, 50)
SL_MULTIPLIER    = 1.5   # SL basato su ATR
TP_MULTIPLIER    = 3.0   # TP basato su ATR
MIN_DAYS_BETWEEN_TRADES = 5  # Numero minimo di giorni tra due ingressi

class NR7FiltredStrategy(Strategy):
    last_trade_date = None
    nr7_high = None
    nr7_low = None

    def init(self):
        self.range7 = self.I(self.compute_nr7_range)
        self.atr = self.I(self.compute_atr, self.data.High, self.data.Low, self.data.Close, 14)
        self.adx = self.I(self.compute_adx, self.data.High, self.data.Low, self.data.Close, 14)
        self.ema9 = self.I(self.ema, self.data.Close, 9)
        self.ema21 = self.I(self.ema, self.data.Close, 21)

    def compute_nr7_range(self):
        high = self.data.High
        low = self.data.Low
        ranges = pd.Series(high - low)
        is_nr7 = ranges.rolling(7).apply(lambda x: x[-1] == min(x), raw=True)
        return is_nr7.fillna(0).astype(bool).values

    def compute_atr(self, high, low, close, period=14):
        high = pd.Series(high)  # Converti in Pandas Series
        low = pd.Series(low)
        close = pd.Series(close)

        tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
        atr = tr.rolling(period).mean()

        return atr.fillna(method='bfill').values

    def compute_adx(self, high, low, close, period=14):
        # Converti in Pandas Series per usare shift() e rolling()
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)

        # True Range (TR)
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # ATR (Average True Range)
        atr = tr.rolling(period).mean()

        # Direzionali DM+ e DM-
        dm_plus = np.where((high - high.shift(1) > low.shift(1) - low) & (high - high.shift(1) > 0),
                           high - high.shift(1), 0)
        dm_minus = np.where((low.shift(1) - low > high - high.shift(1)) & (low.shift(1) - low > 0), low.shift(1) - low,
                            0)

        # Media su N periodi
        dm_plus = pd.Series(dm_plus).rolling(period).mean()
        dm_minus = pd.Series(dm_minus).rolling(period).mean()

        # Indici Direzionali (+DI e -DI)
        di_plus = (dm_plus / atr) * 100
        di_minus = (dm_minus / atr) * 100

        # Indice DX
        dx = (abs(di_plus - di_minus) / (di_plus + di_minus).replace(0, np.nan)) * 100  # Evita divisione per zero

        # ADX finale (media di DX)
        adx = pd.Series(dx).rolling(period).mean()

        # Rimuovi NaN e riempi con backward fill
        return adx.fillna(method='bfill').values

    def ema(self, close, period=9):
        return pd.Series(close).ewm(span=period, adjust=False).mean().values

    def next(self):
        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        # ❌ Esci da ogni posizione alla fine della giornata
        if self.position and current_time >= EXIT_TIME:
            self.position.close()
            self.last_trade_date = None
            return

        # ⏳ Se fuori dalla fascia oraria, non entra
        if not (ENTRY_START_TIME <= current_time <= ENTRY_END_TIME):
            return

        # ⏳ Se già abbiamo tradato recentemente, saltiamo
        if self.last_trade_date and (current_date - self.last_trade_date).days < MIN_DAYS_BETWEEN_TRADES:
            return

        # 📏 Se la candela precedente era NR7, salviamo high/low
        if self.range7[-2]:
            self.nr7_high = self.data.High[-2]
            self.nr7_low  = self.data.Low[-2]

        # 🔍 Verifica condizioni per entrare
        if self.nr7_high and self.nr7_low:
            close = self.data.Close[-1]
            open_ = self.data.Open[-1]
            high = self.data.High[-1]
            low = self.data.Low[-1]

            # 🔹 1️⃣ Filtro ADX (evita mercati laterali)
            if self.adx[-1] < 20:
                return

            # 🔹 2️⃣ Filtro ATR (evita giornate troppo volatili)
            if self.atr[-1] > np.mean(self.atr[-20:]) * 1.5:
                return

            # 🔹 3️⃣ Filtro range normale
            daily_range = high - low
            recent_ranges = self.data.High - self.data.Low
            if len(recent_ranges) < 10:
                return
            avg_range = pd.Series(recent_ranges[-10:]).mean()
            if not (0.8 * avg_range < daily_range < 1.2 * avg_range):
                return

            # 🔹 4️⃣ Filtro breakout pulito (corpo > 50% del range)
            body = abs(close - open_)
            if body < 0.5 * daily_range:
                return

            # 🔹 5️⃣ Filtro volume (solo se volume sopra la media)
            avg_vol = pd.Series(self.data.Volume[-10:]).mean()
            if self.data.Volume[-1] < avg_vol:
                return

            # 🔹 6️⃣ Filtro trend (EMA9 > EMA21 per long, < per short)
            if close > self.nr7_high and self.ema9[-1] > self.ema21[-1] * 1.002:
                sl = close - SL_MULTIPLIER * self.atr[-1]
                tp = close + TP_MULTIPLIER * self.atr[-1]
                self.buy(sl=sl, tp=tp)
                self.last_trade_date = current_date
                self.nr7_high = None
                self.nr7_low = None

            elif close < self.nr7_low and self.ema9[-1] < self.ema21[-1] * 0.998:
                sl = close + SL_MULTIPLIER * self.atr[-1]
                tp = close - TP_MULTIPLIER * self.atr[-1]
                self.sell(sl=sl, tp=tp)
                self.last_trade_date = current_date
                self.nr7_high = None
                self.nr7_low = None
