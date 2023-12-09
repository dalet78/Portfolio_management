import json
import pandas as pd
from libs.filtered_stock import return_filtred_list
from Reports.report_builder import ReportGenerator
from backtesting import Backtest, Strategy
from Trading.methodology.blocked_stock.blocked_stock import TradingAnalyzer
class IntNumber(Strategy):
    def init(self):
        # Presumo che 'self.data' sia già un DataFrame fornito dalla libreria di backtesting
        # Converti l'indice in DateTimeIndex se necessario
        if not isinstance(self.data.index, pd.DatetimeIndex):
            self.data.index = pd.to_datetime(self.data.index)
        self.price = self.data.Close
        # Ora crea il DataFrame pandas_data senza la necessità di manipolare ulteriormente la colonna 'Date'
        self.data['Date'] = pd.to_datetime(self.data['Date'])
        self.data.set_index('Date', inplace=True)
        self.pandas_data = pd.DataFrame({attr: getattr(self.data, attr) for attr in self.data.names})


        enhanced_strategy = TradingAnalyzer(self.pandas_data)
        self.result, image = enhanced_strategy.check_signal()
        if isinstance(self.result, dict):
            trade_type = self.result["details"]["position"]
            trade_date = self.result["details"]["trade_date"]

        else:
            print("accesso non trovato")
            trade_type = self.result["details"]["position"]
            trade_date = self.result["details"]["trade_date"]

    def next(self):
        if self.result['details']['support'] == "interesting_below_resistance":
            resistance_level = self.result['details']['support']
            should_enter = True
        elif self.result['details']['support'] == "interesting_above_support":
            support_level = self.result['details']['support']
            should_enter = True
        else:
            should_enter = False

        if should_enter:
            if self.data.Close[-1] >= resistance_level and not self.position:
                if not self.position:
                    self.buy()
            elif self.data.Close[-1] <= support_level and not self.position:
                if not self.position:
                    self.sell()
        else:
            if self.position.is_long:
                if self.data.Close[-1] > self.result["details"]["take_profit"]:
                    self.position.close()
                elif self.data.Close[-1] < self.result["details"]["stop_loss"]:
                    self.position.close()
            elif self.position.is_short:
                if self.data.Close[-1] < self.result["details"]["take_profit"]:
                    self.position.close()
                elif self.data.Close[-1] > self.result["details"]["stop_loss"]:
                    self.position.close()
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

                data['Date'] = pd.to_datetime(data['Date'])
                data.set_index('Date', inplace=True)

                bt = Backtest(data, IntNumber, commission=.002, exclusive_orders=True)
                stats = bt.run()
                print(stats)
                report.add_content(stats)
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