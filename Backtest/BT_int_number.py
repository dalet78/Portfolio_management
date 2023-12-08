import json
import pandas as pd
from libs.filtered_stock import return_filtred_list
from Reports.report_builder import ReportGenerator
from backtesting import Backtest, Strategy
from Trading.methodology.blocked_stock.blocked_stock import TradingAnalyzer
class IntNumber(Strategy):
    def init(self):
        self.price = self.data.Close
        enhanced_strategy = TradingAnalyzer(self.data)
        self.result, image = enhanced_strategy.check_signal(use_previous_day=True)
        # if self.result: print ("True")

    def next(self):
        if self.result["details"]["position"]== "buy" and self.price > self.result["details"]["enter_price"]:
                self.buy()
        elif self.result["details"]["position"]== "sell" and self.price < self.result["details"]["enter_price"]:
                self.sell()
def main(index="Russel"):
    source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Report blocked stock")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

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
                bt.plot()
            except FileNotFoundError:
            # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
            # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")

        # Salva il report e pulisci i file temporanei
    file_report = report.save_report(filename=f"{index}_Report_blocked_stock")
    return file_report

if __name__ == '__main__':
    main()