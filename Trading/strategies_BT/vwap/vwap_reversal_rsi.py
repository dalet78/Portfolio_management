import backtrader as bt
from datetime import time
import pandas as pd

# Definizione del feed con VWAP
class PandasDataWithVWAP(bt.feeds.PandasData):
    lines = ('vwap',)
    params = (('vwap', 'VWAP'),)

# Strategia VWAPReversal con filtro RSI
class VWAPReversalRSI(bt.Strategy):
    params = dict(
        entry_threshold=0.014,   # Soglia per il segnale di ingresso
        sl_percent=0.007,        # Percentuale per stop loss
        entry_start=time(15, 30),
        entry_end=time(17, 30),
        exit_time=time(19, 50),
        rsi_period=14,           # Periodo per il calcolo dell'RSI
        rsi_overbought=70,       # Soglia RSI per short (ipercomprato)
        rsi_oversold=30 ,        # Soglia RSI per long (ipervenduto)
        reward_to_risk_ratio=2.0,
        max_tp_ratio=0.05  # massimo 5% tra prezzo e TP
    )

    def __init__(self):
        self.order = None
        self.last_trade_date = None
        # Aggiungiamo l'indicatore RSI basato sul close
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)

    def next(self):
        dt = self.datas[0].datetime.datetime(0)
        price = self.datas[0].close[0]
        high = self.datas[0].high[0]
        low = self.datas[0].low[0]
        vwap = self.datas[0].vwap[0]
        rsi_val = self.rsi[0]  # Valore RSI corrente



        current_time = dt.time()
        current_date = dt.date()

        # Chiudi la posizione se è raggiunto l'orario di exit
        if self.position and current_time >= self.p.exit_time:
            self.close()

        # Condizioni per aprire una nuova posizione (una volta per data)
        elif (self.last_trade_date != current_date and
              self.p.entry_start <= current_time <= self.p.entry_end and
              not self.position):

            cash = self.broker.get_cash()

            # 🟢 LONG
            if ((vwap - low) / vwap >= self.p.entry_threshold) and (rsi_val <= self.p.rsi_oversold):
                sl = low - self.p.sl_percent * low
                risk = price - sl
                tp = price + self.p.reward_to_risk_ratio * risk
                size = int(cash / price) if price > 0 else 0
                if abs(tp - price) / price > self.p.max_tp_ratio:
                    print(f"[{dt}] ⚠️ TP troppo distante per LONG: {tp:.2f} (>{self.p.max_tp_ratio * 100:.1f}%)")
                    return

                if tp > price and sl < price and size > 0:
                    self.buy_bracket(price=price, stopprice=sl, limitprice=tp, size=size)
                    self.last_trade_date = current_date

                    profit_per_share = tp - price
                    total_profit = profit_per_share * size

                    # print(
                    #     f"[{dt}] 🟢 LONG | Entry: {price:.2f} | TP: {tp:.2f} | SL: {sl:.2f} | RSI: {rsi_val:.2f} | Size: {size}")
                    # print(f"   ➕ Profit per share: {profit_per_share:.2f} | Total potential profit: {total_profit:.2f}")

            # 🔻 SHORT
            elif ((high - vwap) / vwap >= self.p.entry_threshold) and (rsi_val >= self.p.rsi_overbought):
                sl = high + self.p.sl_percent * high
                risk = sl - price
                tp = price - self.p.reward_to_risk_ratio * risk
                size = int(cash / price) if price > 0 else 0

                # 🛑 Filtro per evitare TP troppo distanti
                if abs(tp - price) / price > self.p.max_tp_ratio:
                    print(f"[{dt}] ⚠️ TP troppo distante per SHORT: {tp:.2f} (>{self.p.max_tp_ratio * 100:.1f}%)")
                    return

                if tp < price and sl > price and size > 0:
                    self.sell_bracket(price=price, stopprice=sl, limitprice=tp, size=size)
                    self.last_trade_date = current_date

                    profit_per_share = price - tp
                    total_profit = profit_per_share * size

                    # print(
                    #     f"[{dt}] 🔻 SHORT | Entry: {price:.2f} | TP: {tp:.2f} | SL: {sl:.2f} | RSI: {rsi_val:.2f} | Size: {size}")
                    # print(f"   ➕ Profit per share: {profit_per_share:.2f} | Total potential profit: {total_profit:.2f}")