import json
import pandas as pd
from libs.filtered_stock import return_filtred_list
from Reports.report_builder import ReportGenerator
from backtesting import Backtest, Strategy
from Trading.methodology.blocked_stock.blocked_stock import TradingAnalyzer
class IntNumber(Strategy):
    def init(self):
        enhanced_strategy = TradingAnalyzer(self.data.df)
        result, image, self.new_data = enhanced_strategy.check_signal(period=20)
        filtred_interesting_dataset =self.new_data[self.new_data['is_interesting'] != 0]
        count_interesting = filtred_interesting_dataset['is_interesting'].count()
        filtred_signal_dataset = self.new_data[self.new_data['signal'] != 0]
        count_signal = filtred_signal_dataset['signal'].count()
        print(count_interesting)
        print(count_signal)

    def next(self):
        if self.new_data.signal ==1:
            self.sell()
        elif self.new_data.signal ==2:
            self.buy()

def main(index="Russel"):
    source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Backtest stock int price")

    tickers_list = return_filtred_list(index=index)
    # Controlla se la lista dei ticker è vuota
    if not tickers_list:
        # Aggiungi un messaggio nel report o registra un log

        report.add_content("Nessun ticker soddisfa i criteri di selezione.")
        print("Nessun ticker soddisfa i criteri di selezione.")
    else:

        for item in tickers_list:
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv")
                bt = Backtest(data, IntNumber, commission=.002, exclusive_orders=True)
                stats = bt.run()
                print(stats)
                report.add_content(content=stats)
            except FileNotFoundError:
            # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
            # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")

        # Salva il report e pulisci i file temporanei
    file_report = report.save_report(filename=f"{index}_Backtest_int_price")
    return file_report

if __name__ == '__main__':
    main()