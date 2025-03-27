from datetime import time
from backtesting import Backtest, Strategy
import numpy as np

# Orari strategia
STRATEGY_START_TIME = time(16, 00)  # Inizia 1 ora dopo l'apertura
STRATEGY_END_TIME = time(17, 00)  # Termina dopo 2 ore
FORCE_EXIT_TIME = time(20, 50)  # **Chiude tutte le posizioni a fine giornata**


class PivotVWAPStrategy(Strategy):
    SL_PERCENT = 0.007  # 0.7%
    TP_PERCENT = 0.014  # 1.4%
    ATR_MULTIPLIER = 1.5  # 🔹 Evita trade su bassa volatilità
    RSI_LONG_THRESHOLD = 55  # 🔹 RSI sopra questo livello per LONG
    RSI_SHORT_THRESHOLD = 45  # 🔹 RSI sotto questo livello per SHORT
    VOLUME_THRESHOLD = 0.7  # 🔹 Evita trade su bassi volumi (70% della media)

    last_trade_date_long = None
    last_trade_date_short = None

    def init(self):
        self.atr_values = self.I(self.atr, self.data.High, self.data.Low, self.data.Close, 14)
        self.rsi_values = self.I(self.rsi, self.data.Close, 14)
        self.volume_avg = self.I(self.sma, self.data.Volume, 20)  # 🔹 Media Volume 20 periodi

    def next(self):
        if len(self.data.Close) < 20:  # 🔹 Evitiamo problemi con ATR, RSI e Volume
            return

        # Otteniamo l'orario e la data attuale
        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()

        # **Chiusura forzata delle operazioni prima della fine della sessione**
        if current_time >= FORCE_EXIT_TIME:
            if self.position:
                self.position.close()
                #print(f"🚨 Chiusura forzata di tutte le posizioni alle {current_time}")
            return

        # **Filtro orario: Eseguiamo trade solo tra 10:30 e 11:30**
        if not (STRATEGY_START_TIME <= current_time <= STRATEGY_END_TIME):
            return

        # **Se c'è già una posizione aperta, non apriamo nuove posizioni**
        if self.position:
            return

        prev_candle_high = self.data.High[-2]
        prev_candle_low = self.data.Low[-2]
        prev_candle_close = self.data.Close[-2]

        vwap = self.data.VWAP[-1]
        atr = self.atr_values[-1]  # 🔹 Volatilità ATR
        rsi = self.rsi_values[-1]  # 🔹 RSI
        volume = self.data.Volume[-1]
        avg_volume = self.volume_avg[-1]  # 🔹 Volume medio
        current_price = self.data.Close[-1]

        # **Debugging**
        #print(f"\n📊 {self.data.index[-1]} - VWAP: {vwap}, ATR: {atr}, RSI: {rsi}, Volume: {volume}, Avg Volume: {avg_volume}")

        # 🔹 **Filtro: Minima volatilità ATR**
        if abs(prev_candle_high - prev_candle_low) < self.ATR_MULTIPLIER * atr:
            #print("⚠️ Skip trade: Volatilità troppo bassa (ATR Filter)")
            return

        # 🔹 **Filtro VWAP Breakout Confirmation** → Il prezzo deve confermare la rottura
        if prev_candle_close < vwap and prev_candle_high > vwap:
            #print("⚠️ Skip trade: Il prezzo non ha confermato il breakout su VWAP")
            return

        # 🔹 **Filtro RSI** → Solo LONG se RSI > 55, SHORT se RSI < 45
        if rsi < self.RSI_LONG_THRESHOLD and rsi > self.RSI_SHORT_THRESHOLD:
            #print("⚠️ Skip trade: RSI neutrale, nessuna conferma di trend forte")
            return

        # 🔹 **Filtro di volume** → Evitiamo trade in momenti di bassa liquidità
        if volume < avg_volume * self.VOLUME_THRESHOLD:
            #print("⚠️ Skip trade: Volume troppo basso rispetto alla media")
            return

        # **Condizioni per LONG**
        if prev_candle_high > vwap:
            if self.last_trade_date_long == current_date:
                #print("⚠️ Skip LONG: Trade già eseguito oggi")
                return

            entry_price = current_price
            stop_loss = entry_price * (1 - self.SL_PERCENT)
            take_profit = entry_price * (1 + self.TP_PERCENT)

            if stop_loss < entry_price < take_profit:
                self.buy(sl=stop_loss, tp=take_profit)
                self.last_trade_date_long = current_date
                #print(f"✅ LONG trade aperto a {entry_price}, SL: {stop_loss}, TP: {take_profit}")

        # **Condizioni per SHORT**
        if prev_candle_low < vwap:
            if self.last_trade_date_short == current_date:
                #print("⚠️ Skip SHORT: Trade già eseguito oggi")
                return

            entry_price = current_price
            stop_loss = entry_price * (1 + self.SL_PERCENT)
            take_profit = entry_price * (1 - self.TP_PERCENT)

            if stop_loss > entry_price > take_profit:
                self.sell(sl=stop_loss, tp=take_profit)
                self.last_trade_date_short = current_date
                #print(f"✅ SHORT trade aperto a {entry_price}, SL: {stop_loss}, TP: {take_profit}")

    @staticmethod
    def sma(series, period=50):
        """Calcola la SMA"""
        return np.convolve(series, np.ones(period) / period, mode='same')

    @staticmethod
    def atr(high, low, close, period=14):
        """Calcola l'ATR in modo compatibile con backtesting.py e mantiene la lunghezza originale"""
        high_low = high - low
        high_close = np.abs(high[1:] - close[:-1])  # Simula shift()
        low_close = np.abs(low[1:] - close[:-1])  # Simula shift()

        tr = np.maximum.reduce([high_low[1:], high_close, low_close])  # True Range
        atr = np.convolve(tr, np.ones(period) / period, mode='valid')  # Media mobile semplice

        # Allineare la lunghezza riempiendo i primi `period` valori con NaN
        atr_full = np.concatenate(([np.nan] * (len(high) - len(atr)), atr))

        return atr_full

    @staticmethod
    def rsi(close, period=14, eps=1e-6):
        """Calcola l'RSI in modo compatibile con backtesting.py evitando la divisione per zero"""
        delta = np.diff(close, prepend=close[0])  # Simula shift senza ridurre la lunghezza
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.convolve(gain, np.ones(period) / period, mode='valid')
        avg_loss = np.convolve(loss, np.ones(period) / period, mode='valid')

        # Evitiamo la divisione per zero sostituendo gli avg_loss = 0 con un valore minimo (eps)
        avg_loss = np.where(avg_loss == 0, eps, avg_loss)

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Allineare la lunghezza riempiendo i primi `period-1` valori con NaN
        rsi_full = np.concatenate(([np.nan] * (len(close) - len(rsi)), rsi))

        return rsi_full
