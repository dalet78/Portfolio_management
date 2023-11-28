import pandas as pd

from portfolio_management.Trading.methodology.breakout_lateral_mov.break_lateral_mov_second import BreakoutSignalAnalyzer_lateral_move_second
from portfolio_management.Reports.report_builder import ReportGenerator
#from portfolio_management.Reports.image_builder import CandlestickChartGenerator
import json

parameters_dict = {}
report= ReportGenerator()
report.add_title(title="Lateral movement breaks analisys second")

with open("portfolio_management/Trading/methodology/strategy_parameter.json", 'r') as file:
    param_data = json.load(file)

for strategy in param_data['Strategies']:
    if strategy['name'] == "breakout_lateral_move_second":
        parameters_dict = strategy['parameters']
        break
with open("portfolio_management/json_files/SP500-short.json", 'r') as file:
        tickers = json.load(file)
        tickers_list = list(tickers.keys())

for item in tickers_list:
    data = pd.read_csv(f"portfolio_management/Trading/Data/Daily/{item}_historical_data.csv")
    analyzer = BreakoutSignalAnalyzer_lateral_move_second(data, parameters_dict)
    # Variabili per il backtest
    total_signals = 0
    buy_signals = 0
    sell_signals = 0
    for i in range(parameters_dict["min_periods"], len(data)):
        # Aggiorna il DataFrame nell'analizzatore con i dati fino al punto corrente
        analyzer.df = data.iloc[:i]

        # Esegui l'analisi
        signal, content, image = analyzer.analyze_range()

        # Registra i risultati
        if signal != 0.0:
            total_signals += 1
            if signal == 1.0:
                buy_signals += 1
            elif signal == -1.0:
                sell_signals += 1
   

    report.add_content(f"{item} Total Signals: {total_signals}")
    report.add_content(f"{item} Buy Signals: {buy_signals}")
    report.add_content(f"{item} Sell Signals: {sell_signals}")

report.save_report(filename="Report_lateral_mov_break_second_backtest")

    