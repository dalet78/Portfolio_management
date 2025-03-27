import talib
from backtesting import Backtest, Strategy
import json
from libs.filtered_stock import return_filtred_list
from datetime import time
from Reports.report_builder import ReportGenerator
from support.data_preparation import DataRefactory

# Strategy Parameters
ENTRY_START_TIME = time(16, 00)  # Entry start time (3:30 PM)
ENTRY_END_TIME = time(17, 30)    # Entry end time (5:30 PM)
EXIT_TIME = time(20, 50)         # Exit time (8:50 PM)
SL_PERCENT = 0.005               # Stop Loss percentage (0.7%)
RSI_PERIOD = 14            # Stop Loss percentage (0.5%)


class VWAPRSIReversalStrategy(Strategy):
    last_trade_date = None

    def init(self):
        global df  # Use a global variable
        super().init()
        self.vwap = self.I(lambda: df['vwap'], name='vwap')
        self.rsi = talib.RSI(df['Close'], timeperiod=14)

    def next(self):
        price = self.data.Close[-1]  # Current price
        high = self.data.High[-1]
        low = self.data.Low[-1]
        current_time = self.data.index[-1].time()  # Current time of the last data point
        current_date = self.data.index[-1].date()  # Current date of the last data point

        if self.position and current_time >= EXIT_TIME:
            self.position.close()  # Chiudi la posizione
            self.last_trade_date = None  # Reset last trade date
            print(f"Posizione chiusa forzatamente alle {EXIT_TIME}")# Reset last trade date

        # Check if it's time to open a new position
        elif (ENTRY_START_TIME <= current_time <= ENTRY_END_TIME and not self.position and
              (self.last_trade_date is None or self.last_trade_date != current_date)):

            # Make a trade and update the last trade date
            self.last_trade_date = current_date

            # Long condition: Price crosses below VWAP and RSI is below 30
            if list(self.data.Close)[-3] < list(self.vwap)[-3] and list(self.rsi)[-3] < 30:
                stop_loss = low - (SL_PERCENT * low)  # SL below current price
                take_profit = self.vwap[-1]  # TP at VWAP
                if take_profit > self.data.Close[-1] and stop_loss < self.data.Close[-1]:
                    self.buy(sl=stop_loss, tp=take_profit)
                else:
                    print(
                        f"Errore: ordine long non valido per  - TP: {take_profit}, LIMIT: {self.data.Close[-1]}, SL: {stop_loss}")

            # Short condition: Price crosses above VWAP and RSI is above 70
            elif list(self.data.Close)[-3] > list(self.vwap)[-3] and list(self.rsi)[-3] > 70:
                stop_loss = high + (SL_PERCENT * high)  # SL above current price
                take_profit = self.vwap[-1]  # TP at VWAP
                if take_profit < self.data.Close[-1] and stop_loss > self.data.Close[-1]:
                    self.sell(sl=stop_loss, tp=take_profit)
                else:
                    print(
                        f"Errore: ordine short non valido per - TP: {take_profit}, LIMIT: {self.data.Close[-1]}, SL: {stop_loss}")



def vwap_rsi_reversal_trading(index="SP500"):
    global df
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} VWAP Reversal with RSI Confirmation Stock")
    report.add_content(f"Trading starts from 4:00 PM\n")

    # Strategy Description
    report.add_content(f"Strategy Description:\n")
    report.add_content(f"1. Timeframe: 5-minute candles\n")
    report.add_content(f"2. Entry window: {ENTRY_START_TIME} - {ENTRY_END_TIME}\n")
    report.add_content(f"3. Exit time: {EXIT_TIME}\n")
    report.add_content(f"4. Buy Condition: Price crosses below VWAP and RSI 14 is below 30 (for long entry)\n")
    report.add_content(f"5. Sell Condition: Price crosses above VWAP and RSI 14 is above 70 (for short entry)\n")
    report.add_content(f"6. Take Profit: Set at the VWAP value, Stop Loss: {SL_PERCENT * 100}% of the current price.\n")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

        tickers_list = return_filtred_list(index=index)
        # Check if the tickers list is empty
        if not tickers_list:
            # Add a message to the report or log it
            print("No tickers meet the selection criteria.")
        else:
            for item in tickers_list:
                print(f'Analyzing stock = {item}')
                try:
                    data_filepath = f"{source_directory}/Data/{index}/5min/{item}_historical_data.csv"
                    df = DataRefactory.prepare_5m_csv(filepath=data_filepath)

                    # Calculate the product of price and volume, and the cumulative volume
                    df['price_volume'] = df['Close'] * df['Volume']
                    # Group by day and calculate the cumulative VWAP for each moment
                    df['cumulative_price_volume'] = df.groupby(df.index.normalize())['price_volume'].cumsum()
                    df['cumulative_volume'] = df.groupby(df.index.normalize())['Volume'].cumsum()
                    df['vwap'] = df['cumulative_price_volume'] / df['cumulative_volume']

                    # Calculate the RSI
                    df['rsi'] = talib.RSI(df['Close'], RSI_PERIOD)

                    # Perform backtesting
                    bt = Backtest(df, VWAPRSIReversalStrategy, cash=10000, exclusive_orders=True)
                    stats = bt.run()


                    total_trades = stats['_trades'].shape[0]
                    win_rate = stats['Win Rate [%]']
                    sharpe_ratio = stats['Sharpe Ratio']
                    max_drawdown = stats['Max. Drawdown [%]']
                    total_return = stats['Return [%]']
                    cagr = stats['CAGR [%]']

                    # Check if the stock meets the criteria
                    if total_trades > 3 and win_rate > 50:
                        # Save the chart in a variable
                        fig = bt.plot()

                        # Add the stock name as the chart title
                        report.add_content(f"Stock = {item}")
                        report.add_content(f"Corresponding Win Rate: {win_rate}%")
                        report.add_content(f"Total Trades = {total_trades}")
                        report.add_content(f"Sharpe Ratio = {sharpe_ratio}")
                        report.add_content(f"Max Drawdown = {max_drawdown}%")
                        report.add_content(f"Total Return = {total_return}%")
                        report.add_content(f"CAGR = {cagr}%\n")

                        print(f'Backtest Performance for {item} (Win Rate: {win_rate}%)')

                except FileNotFoundError:
                    # Handle the error if the file is not found
                    print(f"File not found for {item}")
                except Exception as e:
                    # Handle other generic errors
                    print(f"Error processing {item}: {e}")

    file_report = report.save_report(filename=f"{index}_vwap_rsi_reversal_stock")
    return file_report


# Backtesting preparation
if __name__ == "__main__":
    vwap_rsi_reversal_trading(index="ALL")

