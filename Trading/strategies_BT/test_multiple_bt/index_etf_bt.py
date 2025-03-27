import os
import pandas as pd
import backtrader as bt
from support.data_preparation import DataRefactory
from Trading.strategies_BT.index_difference.diference_spy_etf import PairTradingStrategy

# Paths and settings
DATA_DIRECTORY = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
ALL_DATA_PATH = f"{DATA_DIRECTORY}/Data/INDEX/5min"
CASH = 10000  # Initial capital


def run_backtrader_pair_strategy(stock):
    # Initialize the backtesting engine
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(CASH)
    cerebro.addstrategy(PairTradingStrategy)

    # Add performance analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')

    # Load file paths for SPY and the second asset
    file1 = f"{ALL_DATA_PATH}/SPY_historical_data.csv"
    file2 = f"{ALL_DATA_PATH}/{stock}_historical_data.csv"

    # Check if the files exist
    if not os.path.exists(file1) or not os.path.exists(file2):
        print(f"⚠️ File not found: {file1} or {file2}")
        return

    # Load and preprocess data using custom function
    df1 = DataRefactory.prepare_5m_csv(filepath=file1)
    df2 = DataRefactory.prepare_5m_csv(filepath=file2)

    # Convert pandas DataFrame into Backtrader data feeds
    data1 = bt.feeds.PandasData(dataname=df1, name='SPY')
    data2 = bt.feeds.PandasData(dataname=df2, name=stock)


    cerebro.adddata(data1)
    cerebro.adddata(data2)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    print(f"▶️ Running PairTrading strategy on SPY and {stock}")

    # Execute the strategy
    results = cerebro.run()
    strategy = results[0]

    # Get portfolio performance
    port_value = cerebro.broker.getvalue()
    start_value = cerebro.broker.startingcash
    pnl = port_value - start_value

    print(f"\n💰 Final portfolio value: {port_value:.2f} USD")
    print(f"📈 Net profit: {pnl:.2f} USD")

    # Access analyzers for trade and performance stats
    trades = strategy.analyzers.trades.get_analysis()
    sharpe = strategy.analyzers.sharpe.get_analysis()
    drawdown = strategy.analyzers.drawdown.get_analysis()

    print("\n📊 Trade analysis:")
    print(f"Total closed trades: {trades.total.closed}")
    print(f"Wins: {trades.won.total}")
    print(f"Losses: {trades.lost.total}")
    print(f"Average profit per trade: {trades.pnl.net.average:.2f} USD")
    # Drawdown stats
    print("\n📉 Drawdown analysis:")
    print(f"Maximum drawdown: {drawdown.max.drawdown:.2f}%")
    print(f"Average drawdown: {drawdown.drawdown:.2f}%")

    if sharpe and 'sharperatio' in sharpe:
        print(f"Sharpe Ratio: {sharpe['sharperatio']:.2f}")
    else:
        print("Sharpe Ratio: N/A (not enough data or volatility)")

    # Optionally plot results
    cerebro.addobserver(BrokerCash)
    cerebro.plot(style='candlestick')

class BrokerCash(bt.Observer):
    lines = ('cash',)
    plotinfo = dict(subplot=True, plot=True)

    def next(self):
        self.lines.cash[0] = self._owner.broker.get_cash()

if __name__ == "__main__":
    run_backtrader_pair_strategy(stock="VOO")
