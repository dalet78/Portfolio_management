import pandas as pd
from libs.filtered_stock import return_filtred_list
from Reports.report_builder import ReportGenerator
from Trading.methodology.blocked_stock.blocked_stock import TradingAnalyzer
from Backtest.backtest_class import Backtester

source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
def backtest_full_price(index = "Russel"):
    success_count = 0
    total_trades = 0
    report = ReportGenerator()
    report.add_title(title=f"{index} Report backtest")

    tickers_list = return_filtred_list(index=index)
    # Controlla se la lista dei ticker è vuota
    if not tickers_list:
        # Aggiungi un messaggio nel report o registra un log
        report.add_content("Nessun ticker soddisfa i criteri di selezione.")
        print("Nessun ticker soddisfa i criteri di selezione.")
    else:
        for item in tickers_list:
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv",
                                   parse_dates=['Date'])
                trade_analysis = TradingAnalyzer(data)
                result, image = trade_analysis.check_signal()

                if result:
                    trade_date = result["details"]["trade_date"]
                    start_index = data[data['Date'] == trade_date].index[0]
                    trade_success = execute_trade(dataset=data, start_index=start_index,
                                                  trade_type=result["details"]["position"],
                                                  entry_price=result["details"]["enter_price"],
                                                  stop_loss=result["details"]["stop_loss"],
                                                  take_profit=result["details"]["take_profit"])
                    if trade_success:
                        success_count += 1
                    total_trades += 1

                # Aggiornamento del report
                report.add_content(f'stock = {item}')
                success_rate = (success_count / total_trades) * 100 if total_trades > 0 else 0
                report.add_content(
                    f'total_trades={total_trades}, successful_trades= {success_count}, success_rate ={success_rate}%')
            except FileNotFoundError:
                # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
                # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")

        # Salva il report e pulisci i file temporanei
    file_report = report.save_report(filename=f"{index}_Report_backtest_blocked_stock")
    trade_analysis.clear_img_temp_files()
    return file_report

def execute_trade(dataset, start_index, trade_type, entry_price, stop_loss, take_profit):
    """
     Esegue il trade e determina se è un successo.

     Args:
     - dataset (DataFrame): DataFrame contenente i dati storici dello stock.
     - trade_type (str): 'buy' per acquisto o 'sell' per vendita.
     - entry_price (float): Prezzo a cui il trade viene eseguito.
     - stop_loss (float): Prezzo a cui il trade viene chiuso per limitare le perdite.
     - take_profit (float): Prezzo a cui il trade viene chiuso per realizzare il profitto.

     Returns:
     - bool: True se il trade è riuscito, False altrimenti.
     """

    # Assicurati che i dati siano ordinati per data
    dataset.sort_values('Date', inplace=True)

    for index in range(start_index, len(dataset)):
        row = dataset.iloc[index]
        current_price = row['Close']  # Assumendo che si utilizzi il prezzo di chiusura

        # Logica per un trade di tipo 'buy'
        if trade_type == 'buy':
            if current_price <= stop_loss:
                return False  # Stop-loss colpito
            elif current_price >= take_profit:
                return True  # Take-profit raggiunto

        # Logica per un trade di tipo 'sell'
        elif trade_type == 'sell':
            if current_price >= stop_loss:
                return False  # Stop-loss colpito
            elif current_price <= take_profit:
                return True  # Take-profit raggiunto

    # Se il ciclo termina senza raggiungere take-profit o stop-loss
    return False


if __name__ == '__main__':
    backtest_full_price()
