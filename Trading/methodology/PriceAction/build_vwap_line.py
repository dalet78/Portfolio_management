from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
import pandas as pd
import time
from libs.indicators.vwap_handler import  TradingVWAP
from libs.filtered_stock import return_filtred_list

def vwap_stock_finder(index="Russel"):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Possible vwap stock")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    tickers_list = return_filtred_list(index=index)
    close_to_vwap_stocks = []
    # Controlla se la lista dei ticker è vuota
    if not tickers_list:
        # Aggiungi un messaggio nel report o registra un log
        report.add_content("Nessun ticker soddisfa i criteri di selezione.")
        print("Nessun ticker soddisfa i criteri di selezione.")
    else:

        for item in tickers_list:
            print(f'Analyze stock = {item}')
            result = False
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv",
                                   parse_dates=['Date'])
##############################################################################################
                if not {'Date', 'High', 'Low', 'Open', 'Close', 'Volume'}.issubset(data.columns):
                    raise ValueError(
                        "Il DataFrame deve contenere le colonne 'Date', 'High', 'Low', 'Open', 'Close' e 'Volume'.")

                threshold = 0.2
                trading_vwap = TradingVWAP(data)
                last_close_price = data['Close'].iloc[-1]
                vwap_values = []
                std_devs = []

                # Ottieni i dati per settimana, mese, quadrimestre e anno
                timeframes = [
                    ('Venerdì precedente', trading_vwap.get_previous_friday_vwap_and_std()),
                    ('Ultimo giorno del mese precedente', trading_vwap.get_last_month_vwap_and_std()),
                    ('Ultimo giorno del quadrimestre precedente', trading_vwap.get_last_quarter_vwap_and_std()),
                    ('Ultimo giorno utile dell\'anno precedente', trading_vwap.get_last_year_vwap_and_std())
                ]

                # Controlla la vicinanza del prezzo di chiusura ai valori VWAP
                for label, (vwap, std) in timeframes:
                    vwap_minus_std, vwap_plus_std = vwap - std, vwap + std

                    if abs(last_close_price - vwap_minus_std) <= threshold or \
                            abs(last_close_price - vwap) <= threshold or \
                            abs(last_close_price - vwap_plus_std) <= threshold:
                        close_to_vwap_stocks.append((item, label))
                        exit_values = [vwap_minus_std, vwap, vwap_plus_std]
                        image = CandlestickChartGenerator(data)
                        image_path = image.create_chart_with_horizontal_lines_and_volume(lines=exit_values,
                                                                                         max_points=90)
                        report.add_content(f'Stock = {item} vicino al VWAP del {label}\n')
                        report.add_commented_image(df=data, comment=f'VWAP values = {exit_values}\n',
                                                   image_path=image_path)
                        break

            except FileNotFoundError:
                print(f"File non trovato per {item}")
            except Exception as e:
                print(f"Errore durante l'elaborazione di {item}: {e}")

            file_report = report.save_report(filename=f"{index}_vwap_analysis")
            print(f"Report salvato in: {file_report}")
            duration = time.time() - start_time
            print(f"Tempo di esecuzione: {duration:.2f} secondi")
################################################################################################


if __name__ == '__main__':
    vwap_stock_finder(index = "Nasdaq")
    vwap_stock_finder(index = "SP500")
    #vwap_stock_finder(index="Russel")