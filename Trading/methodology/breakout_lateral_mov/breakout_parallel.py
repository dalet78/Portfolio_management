import pandas as pd
from libs.filtered_stock import return_filtred_list
from libs.PriceChannelDetector import ChannelDetector
from tqdm import tqdm
from backtesting import Strategy
from backtesting import Backtest

def isBreakOut(df, candle, backcandles, window, parallel):
    if (candle-backcandles-window)<0:
        return 0

    chanel_detector = ChannelDetector(df, backcandles, window)
    sl_lows, interc_lows, sl_highs, interc_highs, r_sq_l, r_sq_h = chanel_detector.collect_parallel_channel(candle,
        parallel=parallel)

    prev_idx = candle-1
    prev_high = df.iloc[candle-1].High
    prev_low = df.iloc[candle-1].Low
    prev_close = df.iloc[candle-1].Close

    curr_idx = candle
    curr_high = df.iloc[candle].High
    curr_low = df.iloc[candle].Low
    curr_close = df.iloc[candle].Close
    curr_open = df.iloc[candle].Open

    if ( #prev_high > (sl_lows*prev_idx + interc_lows) and
        #prev_close < (sl_lows*prev_idx + interc_lows) and
        curr_open < (sl_lows*curr_idx + interc_lows) and
        curr_close < (sl_lows*prev_idx + interc_lows) and
        r_sq_l > 0.9 and r_sq_h > 0.9):
        return 1

    elif ( #prev_low < (sl_highs*prev_idx + interc_highs) and
        #prev_close > (sl_highs*prev_idx + interc_highs) and
        curr_open > (sl_highs*curr_idx + interc_highs) and
        curr_close > (sl_highs*prev_idx + interc_highs) and
        r_sq_h > 0.9 and r_sq_l > 0.9):
        return 2

    else:
        return 0

def main():
    index = "Nasdaq"
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    tickers_list = return_filtred_list(index=index)
    with open(f'{source_directory}/Reports/Data/tmp/report_backtest_parallel.txt', 'w') as file:
        file.write("Report\n")
    # Controlla se la lista dei ticker è vuota
    if not tickers_list:
        # Aggiungi un messaggio nel report o registra un log
        # report.add_content("Nessun ticker soddisfa i criteri di selezione.")
        print("Nessun ticker soddisfa i criteri di selezione.")
    else:

        for item in tickers_list:
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv")
                data["isBreakOut"] = [isBreakOut(data, candle=500, backcandles = 40, window = 5, parallel=0.1) for candle in tqdm(data.index)]
                # ChannelDetector.plot_pivot_parallel_channel(data, candle=500, backcandles = 40, window = 5)
                # data[data["isBreakOut"] != 0][:30]
            except FileNotFoundError:
                # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
                # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")
            data['date_column'] = pd.to_datetime(data['Date'])
            data.set_index('date_column', inplace=True)
            bt = Backtest(data, MyStrat, cash=10000, margin=1 / 5)
            stat = bt.run()
            with open(f'{source_directory}/Reports/Data/tmp/report_backtest_parallel.txt', 'a') as file:
                file.write(f"{item}\n {stat}")


class MyStrat(Strategy):
    mysize = 10000
    def init(self):
        super().init()
        self.signal = self.data.isBreakOut

    def next(self):
        super().next()
        TPSLRatio = 1.5
        perc = 0.03


        if self.signal!=0 and len(self.trades)==0 and self.data.isBreakOut==2:
            sl = self.data.Close[-1]-self.data.Close[-1]*perc
            sldiff = abs(sl-self.data.Close[-1])
            tp = self.data.Close[-1]+sldiff*TPSLRatio
            self.buy(sl=sl, tp=tp, size=self.mysize)

        elif self.signal!=0 and len(self.trades)==0 and self.data.isBreakOut==1:
            sl = self.data.Close[-1]+self.data.Close[-1]*perc
            sldiff = abs(sl-self.data.Close[-1])
            tp = self.data.Close[-1]-sldiff*TPSLRatio
            self.sell(sl=sl, tp=tp, size=self.mysize)


if __name__ == '__main__':
    main()
