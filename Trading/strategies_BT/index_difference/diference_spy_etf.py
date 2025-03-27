import csv
import os
import numpy as np
from datetime import datetime
import backtrader as bt

# Optional: Indicator for normalizing asset prices (not used in current strategy)
class NormalizedDiff(bt.Indicator):
    lines = ('diff',)
    plotinfo = dict(subplot=True)

    def __init__(self):
        self.initial_price1 = None
        self.initial_price2 = None

    def next(self):
        if len(self.data0) < 1 or len(self.data1) < 1:
            return

        if self.initial_price1 is None:
            self.initial_price1 = self.data0.close[0]
        if self.initial_price2 is None:
            self.initial_price2 = self.data1.close[0]

        try:
            norm_price1 = self.data0.close[0] / self.initial_price1
            norm_price2 = self.data1.close[0] / self.initial_price2
            self.lines.diff[0] = (norm_price1 - norm_price2) * 100
        except IndexError:
            pass  # Safety check, should rarely happen

# Main indicator used: computes linear regression spread between two assets
class RegressionSpread(bt.Indicator):
    lines = ('spread',)
    params = (('period', 30),)  # Rolling window

    def __init__(self):
        self.addminperiod(self.p.period)

    def next(self):
        y = np.array(self.data0.get(size=self.p.period))
        x = np.array(self.data1.get(size=self.p.period))

        if len(x) < self.p.period or len(y) < self.p.period:
            return

        # Linear regression: y ≈ alpha + beta * x
        A = np.vstack([x, np.ones(len(x))]).T
        beta, alpha = np.linalg.lstsq(A, y, rcond=None)[0]

        y_current = self.data0[0]
        x_current = self.data1[0]
        y_estimated = alpha + beta * x_current

        # Spread = actual - estimated
        self.lines.spread[0] = y_current - y_estimated

# Optional: z-score of the spread (useful to filter noise)
class ZScoreSpread(bt.Indicator):
    lines = ('zscore',)
    params = (('period', 30),)

    def __init__(self):
        self.spread_buffer = []
        self.addminperiod(self.p.period)

    def next(self):
        y = np.array(self.data0.get(size=self.p.period))
        x = np.array(self.data1.get(size=self.p.period))

        if len(x) < self.p.period or len(y) < self.p.period:
            return

        A = np.vstack([x, np.ones(len(x))]).T
        beta, alpha = np.linalg.lstsq(A, y, rcond=None)[0]

        y_current = self.data0[0]
        x_current = self.data1[0]
        y_estimated = alpha + beta * x_current

        spread = y_current - y_estimated
        self.spread_buffer.append(spread)

        if len(self.spread_buffer) > self.p.period:
            self.spread_buffer.pop(0)

        mean = np.mean(self.spread_buffer)
        std = np.std(self.spread_buffer)

        if std != 0:
            self.lines.zscore[0] = (spread - mean) / std

# Main strategy: pair trading based on regression spread
class PairTradingStrategy(bt.Strategy):
    # REGRESSION #
    # params = (
    #     ('entry_threshold', 1.5),
    #     ('exit_threshold', 0.5),
    # )
    #ZSCORE #
    params = dict(
        zentry_upper=3.8,
        zentry_lower=3.2,
        zexit=0.8,
        period=30
    )

    def __init__(self):
        self.asset1 = self.datas[0]
        self.asset2 = self.datas[1]
        self.spread = ZScoreSpread(self.asset1, self.asset2, period=30)
        self.open_trades = {}

        # === CSV Logging Setup ===
        log_dir = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/Data/"
        os.makedirs(log_dir, exist_ok=True)
        self.log_path = os.path.join(
            log_dir, f"pair_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        self.csv_file = open(self.log_path, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'Asset', 'Position Type',
            'Entry Datetime', 'Entry Price',
            'Exit Datetime', 'Exit Price',
            'Size', 'PnL'
        ])

    def log_order(self, asset, order_type, price, size):
        dt = self.datas[0].datetime.datetime(0)
        self.csv_writer.writerow([dt, asset._name, order_type, round(price, 4), round(size, 4)])

    def notify_order(self, order):
        if order.status in [order.Completed]:
            dt = self.datas[0].datetime.datetime(0)
            asset_name = order.data._name
            action = 'BUY' if order.isbuy() else 'SELL'
            price = order.executed.price
            size = order.executed.size

            if order.isbuy():
                if asset_name not in self.open_trades:
                    # LONG ENTRY
                    self.open_trades[asset_name] = {
                        'type': 'LONG',
                        'entry_dt': dt,
                        'entry_price': price,
                        'size': size
                    }
            elif order.issell() and asset_name not in self.open_trades:
                # SHORT ENTRY
                self.open_trades[asset_name] = {
                    'type': 'SHORT',
                    'entry_dt': dt,
                    'entry_price': price,
                    'size': size
                }
            else:
                # EXIT TRADE
                entry = self.open_trades.pop(asset_name, None)
                if entry:
                    entry_price = entry['entry_price']
                    entry_dt = entry['entry_dt']
                    position_type = entry['type']
                    size = entry['size']
                    exit_price = price
                    exit_dt = dt

                    if position_type == 'LONG':
                        pnl = (exit_price - entry_price) * size
                    else:  # SHORT
                        pnl = (entry_price - exit_price) * size

                    pnl = round(pnl, 2)

                    self.csv_writer.writerow([
                        asset_name,
                        position_type,
                        entry_dt, round(entry_price, 4),
                        exit_dt, round(exit_price, 4),
                        round(size, 4),
                        pnl
                    ])

    #REGRESSION
    # def next(self):
    #     spread = self.spread[0]
    #     has_position = (
    #         self.getposition(self.asset1).size != 0 or
    #         self.getposition(self.asset2).size != 0
    #     )
    #
    #     cash = self.broker.get_cash()
    #     price1 = self.asset1.close[0]
    #     price2 = self.asset2.close[0]
    #     size1 = (cash) / price1
    #     size2 = (cash) / price2
    #
    #     if not has_position:
    #         if spread > self.params.entry_threshold:
    #             # self.sell(self.asset1, size=size1)
    #             self.buy(self.asset2, size=size2)
    #         elif spread < -self.params.entry_threshold:
    #             # self.buy(self.asset1, size=size1)
    #             self.sell(self.asset2, size=size2)
    #
    #     else:
    #         if abs(spread) < self.params.exit_threshold:
    #             self.close(self.asset1)
    #             self.close(self.asset2)


    #ZSCORE
    def next(self):
        zscore = self.spread.zscore[0]

        has_position = (
                self.getposition(self.asset1).size != 0 or
                self.getposition(self.asset2).size != 0
        )

        cash = self.broker.get_cash()
        price1 = self.asset1.close[0]
        price2 = self.asset2.close[0]
        size1 = cash / price1
        size2 = cash / price2

        if not has_position:
            if self.p.zentry_lower <= zscore <= self.p.zentry_upper:
                #self.sell(self.asset1, size=size1)
                self.sell(self.asset2, size=size2)
            elif -self.p.zentry_upper <= zscore <= -self.p.zentry_lower:
                #self.buy(self.asset1, size=size1)
                self.buy(self.asset2, size=size2)

        else:
            if abs(zscore) < self.p.zexit:
                # self.close(self.asset1)
                self.close(self.asset2)

    def stop(self):
        self.csv_file.close()
        print(f"\n📄 Trade log saved to: {self.log_path}")
