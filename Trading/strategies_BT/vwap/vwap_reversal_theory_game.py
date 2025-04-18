import backtrader as bt
from datetime import time

class PandasDataWithVWAP(bt.feeds.PandasData):
    lines = ('vwap',)
    params = (('vwap', 'VWAP'),)

class VWAPReversalTheoryGames(bt.Strategy):
    params = dict(
        entry_threshold=0.014,
        sl_percent=0.007,
        entry_start=time(15, 30),
        entry_end=time(17, 0),
        exit_time=time(19, 50),
        reward_to_risk_ratio=2.0,
        max_tp_ratio=0.05  # massimo 5% tra prezzo e TP
    )

    def __init__(self):
        self.order = None
        self.last_trade_date = None
        # ✅ Media mobile del volume per calcolare volume_ratio
        self.volume_ma = bt.indicators.SimpleMovingAverage(self.datas[0].volume, period=20)

    def next(self):
        dt = self.datas[0].datetime.datetime(0)
        price = self.datas[0].close[0]
        high = self.datas[0].high[0]
        low = self.datas[0].low[0]
        vwap = self.datas[0].vwap[0]

        current_time = dt.time()
        current_date = dt.date()

        # ⚠️ Esci se sei in posizione e l'orario di uscita è arrivato
        if self.position and current_time >= self.p.exit_time:
            self.close()

        # ✅ Finestra operativa
        elif (self.last_trade_date != current_date and
              self.p.entry_start <= current_time <= self.p.entry_end and
              not self.position):

            volume = self.datas[0].volume[0]
            volume_ma = self.volume_ma[0]
            volume_ratio = volume / volume_ma if volume_ma > 0 else 1

            cash = self.broker.get_cash()
            size = int(cash / price) if price > 0 else 0

            # 🟢 LONG
            if (vwap - low) / vwap >= self.p.entry_threshold and volume_ratio < 2.0:
                sl = low - self.p.sl_percent * low
                tp = vwap

                if abs(tp - price) / price > self.p.max_tp_ratio:
                    print(f"[{dt}] ⚠️ TP troppo distante per LONG: {tp:.2f} (>{self.p.max_tp_ratio * 100:.1f}%)")
                    return

                if tp > price and sl < price and size > 0:
                    self.buy_bracket(price=price, stopprice=sl, limitprice=tp, size=size)
                    self.last_trade_date = current_date

            # 🔻 SHORT
            elif (high - vwap) / vwap >= self.p.entry_threshold and volume_ratio < 2.0:
                sl = high + self.p.sl_percent * high
                tp = vwap

                if abs(tp - price) / price > self.p.max_tp_ratio:
                    print(f"[{dt}] ⚠️ TP troppo distante per SHORT: {tp:.2f} (>{self.p.max_tp_ratio * 100:.1f}%)")
                    return

                if tp < price and sl > price and size > 0:
                    self.sell_bracket(price=price, stopprice=sl, limitprice=tp, size=size)
                    self.last_trade_date = current_date
