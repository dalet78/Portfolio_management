import backtrader as bt
from datetime import time

class PandasDataWithVWAP(bt.feeds.PandasData):
    lines = ('vwap',)
    params = (('vwap', 'VWAP'),)

class VWAPReversalTheoryGamesDoubleAgents(bt.Strategy):
    params = dict(
        entry_threshold=0.014,
        sl_percent=0.007,
        entry_start=time(15, 30),
        entry_end=time(17, 0),
        exit_time=time(19, 50),
        reward_to_risk_ratio=2.0,
        max_tp_ratio=0.05,
        breakout_volume_ratio=2.0  # soglia per attivare il breakout agent
    )

    def __init__(self):
        self.order = None
        self.last_trade_date = None
        self.volume_ma = bt.indicators.SimpleMovingAverage(self.datas[0].volume, period=20)

    def next(self):
        dt = self.datas[0].datetime.datetime(0)
        price = self.datas[0].close[0]
        high = self.datas[0].high[0]
        low = self.datas[0].low[0]
        vwap = self.datas[0].vwap[0]

        current_time = dt.time()
        current_date = dt.date()

        if self.position and current_time >= self.p.exit_time:
            self.close()

        elif (self.last_trade_date != current_date and
              self.p.entry_start <= current_time <= self.p.entry_end and
              not self.position):

            volume = self.datas[0].volume[0]
            volume_ma = self.volume_ma[0]
            volume_ratio = volume / volume_ma if volume_ma > 0 else 1

            cash = self.broker.get_cash()
            size = int(cash / price) if price > 0 else 0

            # === AGENTE REVERSAL ===
            if (vwap - low) / vwap >= self.p.entry_threshold and volume_ratio < self.p.breakout_volume_ratio:
                sl = low - self.p.sl_percent * low
                tp = vwap
                if abs(tp - price) / price <= self.p.max_tp_ratio and tp > price and sl < price and size > 0:
                    self.buy_bracket(price=price, stopprice=sl, limitprice=tp, size=size)
                    self.last_trade_date = current_date
                    print(f"[{dt}] 🔄 REVERSAL LONG | VolumeRatio: {volume_ratio:.2f}")

            elif (high - vwap) / vwap >= self.p.entry_threshold and volume_ratio < self.p.breakout_volume_ratio:
                sl = high + self.p.sl_percent * high
                tp = vwap
                if abs(tp - price) / price <= self.p.max_tp_ratio and tp < price and sl > price and size > 0:
                    self.sell_bracket(price=price, stopprice=sl, limitprice=tp, size=size)
                    self.last_trade_date = current_date
                    print(f"[{dt}] 🔄 REVERSAL SHORT | VolumeRatio: {volume_ratio:.2f}")

            # === AGENTE BREAKOUT ===
            elif (vwap - low) / vwap >= self.p.entry_threshold and volume_ratio >= self.p.breakout_volume_ratio:
                sl = price - self.p.sl_percent * price
                tp = price + self.p.reward_to_risk_ratio * (price - sl)
                if abs(tp - price) / price <= self.p.max_tp_ratio and tp > price and sl < price and size > 0:
                    self.buy_bracket(price=price, stopprice=sl, limitprice=tp, size=size)
                    self.last_trade_date = current_date
                    print(f"[{dt}] 🚀 BREAKOUT LONG | VolumeRatio: {volume_ratio:.2f}")

            elif (high - vwap) / vwap >= self.p.entry_threshold and volume_ratio >= self.p.breakout_volume_ratio:
                sl = price + self.p.sl_percent * price
                tp = price - self.p.reward_to_risk_ratio * (sl - price)
                if abs(tp - price) / price <= self.p.max_tp_ratio and tp < price and sl > price and size > 0:
                    self.sell_bracket(price=price, stopprice=sl, limitprice=tp, size=size)
                    self.last_trade_date = current_date
                    print(f"[{dt}] 🚀 BREAKOUT SHORT | VolumeRatio: {volume_ratio:.2f}")
