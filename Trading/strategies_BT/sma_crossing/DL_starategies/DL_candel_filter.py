from backtesting import Backtest, Strategy
from backtesting.test import SMA
from datetime import time
from joblib import load
import pandas as pd

ENTRY_START_TIME = time(13, 30)
ENTRY_END_TIME = time(13, 50)
EXIT_TIME = time(20, 50)
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SL_PERCENT = 0.007
TP_PERCENT = 0.014

class HOLC_DL_Strategy_Candle(Strategy):
    last_trade_date = None
    trade_results = []

    def init(self):
        super().init()
        price = self.data.Close
        self.ma1 = self.I(SMA, price, SMA_SHORT_PERIOD)
        self.ma2 = self.I(SMA, price, SMA_LONG_PERIOD)

        self.model_buy = load("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Models/model_sma3candle_buy.joblib")
        self.model_sell = load("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Models/model_sma3candle_sell.joblib")

    def _predict_buy_signal(self):
        df = pd.DataFrame({
            "SMA_5": [float(self.ma1[-1])],
            "SMA_20": [float(self.ma2[-1])],
            "sma_ratio": [float(self.ma1[-1]) / float(self.ma2[-1])],
            "volume_ratio": [float(self.data.Volume[-1]) / max(float(self.data.Volume[-20:].mean()), 1)],
            # "VWAP": [float(self.data.VWAP[-1])],
            "gap": [float(self.data.Open[-1]) - float(self.data.Close[-2])],
            # "RSI_14": [float(self.data.RSI_14[-1])],
            "ATR_14": [float(self.data.ATR_14[-1])],
        })

        df = df.astype(float)  # Garantisce che LightGBM non dia errore
        prob = self.model_buy.predict_proba(df)[0][1]
        return prob > 0.5

    def _predict_sell_signal(self):
        df = pd.DataFrame({
            "SMA_5": [float(self.ma1[-1])],
            "SMA_20": [float(self.ma2[-1])],
            "sma_ratio": [float(self.ma1[-1]) / float(self.ma2[-1])],
            "volume_ratio": [float(self.data.Volume[-1]) / max(float(self.data.Volume[-20:].mean()), 1)],
            # "VWAP": [float(self.data.VWAP[-1])],
            "gap": [float(self.data.Open[-1]) - float(self.data.Close[-2])],
            # "RSI_14": [float(self.data.RSI_14[-1])],
            "ATR_14": [float(self.data.ATR_14[-1])],
        })

        df = df.astype(float)
        prob = self.model_sell.predict_proba(df)[0][1]
        return prob > 0.5

    def next(self):
        if len(self.data.Close) < 25:  # per volume_ratio a 20
            return

        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()
        sma1 = self.ma1[-2]
        sma2 = self.ma2[-2]
        sma1_prev = self.ma1[-3]
        sma2_prev = self.ma2[-3]
        entry_price = self.data.Open[-1]

        if self.position:
            last_trade = self.trades[-1]
            if last_trade and last_trade.pl is not None:
                self.trade_results.append(1 if last_trade.pl > 0 else -1)
                self.last_trade_date = None

        elif ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and (
                self.last_trade_date is None or self.last_trade_date != current_date):

            # BUY
            if sma1 > sma2 and sma1_prev <= sma2_prev and self._predict_buy_signal():
                sl = entry_price - SL_PERCENT * entry_price
                tp = entry_price + TP_PERCENT * entry_price
                self.buy(limit=entry_price, sl=sl, tp=tp)

            # SELL
            elif sma1 < sma2 and sma1_prev >= sma2_prev and self._predict_sell_signal():
                sl = entry_price + SL_PERCENT * entry_price
                tp = entry_price - TP_PERCENT * entry_price
                self.sell(limit=entry_price, sl=sl, tp=tp)

            self.last_trade_date = current_date
