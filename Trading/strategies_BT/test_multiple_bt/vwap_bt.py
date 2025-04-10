import os
import pandas as pd
import numpy as np
from backtesting import Backtest
import backtrader as bt
from libs.filtered_stock import return_filtred_list
from support.data_preparation import DataRefactory
from libs.level_creation.vwap_calc import VWAPCalculator
from Trading.strategies_BT.vwap.vwap_reversal_new import VWAPReversal, PandasDataWithVWAP
from Trading.strategies_BT.vwap.vwap_reversal_rsi import VWAPReversalRSI
# from Trading.strategies_BT.vwap.vwap_reversal import VWAPReversalStrategy

# Costanti
DATA_DIRECTORY = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
ALL_DATA_PATH = f"{DATA_DIRECTORY}/Data/ALL/1min"
REPORT_DIRECTORY = f"{DATA_DIRECTORY}/Reports/Data"
REPORT_FILEPATH = f"{REPORT_DIRECTORY}/vwap_diff_strategy_high_risk_1500_tot.csv"
CSV_BACKTEST = f"{REPORT_DIRECTORY}/vwap_diff_strategy_high_risk_1430_tot_trade.csv"
COMMISSION_PER_TRADE = 2  # Commissione fissa per operazione
RESULT_COLUMNS = [
    "Stock", "Strategy", "Win Rate", "Max Drawdown", "Return [%]", "Total Trades",
        "Total Commissions [$]", "Net Return [%]", "CAGR [%]", "Sharpe Ratio"
]

# Creazione della directory dei report se non esiste
os.makedirs(REPORT_DIRECTORY, exist_ok=True)

# Lista degli stock e strategie da testare
filtered_stocks = return_filtred_list(index="ALL") #["MRNA"] #
strategies = [VWAPReversal, VWAPReversalRSI]

def run_backtest_for_stock(stock, strategies):
    results = []
    all_trades = []

    try:
        data_filepath = f"{ALL_DATA_PATH}/{stock}_historical_data.csv"
        if not os.path.exists(data_filepath):
            print(f"❌ File non trovato: {data_filepath}")
            return results, all_trades

        df = DataRefactory.prepare_min_csv(filepath=data_filepath)
        vwap_calculator = VWAPCalculator(df)
        df = vwap_calculator.calculate_vwap_daily()

        # Optional: salva il file con VWAP
        # df.to_csv(f"{REPORT_DIRECTORY}/{stock}_vwap.csv")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError(f"Indice non è DatetimeIndex per {stock}")
        if df.index.hasnans:
            raise ValueError(f"Indice contiene valori nulli per {stock}")

        for strategy in strategies:
            try:
                cerebro = bt.Cerebro()
                cerebro.addstrategy(strategy)

                data = PandasDataWithVWAP(dataname=df)
                cerebro.adddata(data)
                cerebro.broker.set_cash(10000)

                # Analizzatori
                cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
                cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
                cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
                cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
                cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
                cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

                print(f"🚀 Running backtest for {stock} with {strategy.__name__}...")
                results_list = cerebro.run()
                print("✅ Backtest finished.")

                strat_instance = results_list[0]

                # Estrazione analyzer
                stats = strat_instance.analyzers.trade_analyzer.get_analysis()
                returns_analysis = strat_instance.analyzers.returns.get_analysis()
                drawdown_analysis = strat_instance.analyzers.drawdown.get_analysis()
                sharpe_analysis = strat_instance.analyzers.sharpe.get_analysis()
                annual_returns = strat_instance.analyzers.annual_return.get_analysis()
                ta = strat_instance.analyzers.trades.get_analysis()

                # Print base summary (con fallback sicuro)
                if hasattr(strat_instance.analyzers, 'trades'):
                    ta = strat_instance.analyzers.trades.get_analysis()
                    print(f"📊 TRADE SUMMARY for {stock} - {strategy.__name__}")
                    print(f"Total closed trades: {ta.get('total', {}).get('closed', 0)}")
                    print(f"Winning trades: {ta.get('won', {}).get('total', 0)}")
                    print(f"Losing trades: {ta.get('lost', {}).get('total', 0)}")
                    print(f"Net profit: {ta.get('pnl', {}).get('net', {}).get('total', 0):.2f}")
                    print(f"Average profit per trade: {ta.get('pnl', {}).get('net', {}).get('average', 0):.2f}")
                else:
                    print(f"⚠️ Analyzer 'trades' non trovato per {stock} - {strategy.__name__}")

                # Total closed trades
                total_trades = stats.get('total', {}).get('closed', 0)

                # Trade vincenti
                won_trades = stats.get('won', {}).get('total', 0)

                # Win rate
                win_rate = (won_trades / total_trades * 100) if total_trades else 0

                # Commissioni totali
                total_commissions = total_trades * COMMISSION_PER_TRADE

                # Return lordo
                gross_return = returns_analysis.get('rtot', 0) * 100

                # Return netto
                broker_value = cerebro.broker.getvalue()
                net_return = round(gross_return - (total_commissions / broker_value * 100),
                                   2) if broker_value else gross_return

                # Profitto massimo
                max_profit = stats.get('won', {}).get('pnl', {}).get('max', 0)

                # Perdita massima (valore assoluto)
                max_loss = abs(stats.get('lost', {}).get('pnl', {}).get('max', 0))

                # Risultati aggregati per CSV
                results.append({
                    "Stock": stock,
                    "Strategy": strategy.__name__,
                    "Win Rate": round(win_rate, 2),
                    "Max Drawdown": round(drawdown_analysis.get('max', {}).get('drawdown', 0), 2),
                    "Return [%]": round(gross_return, 2),
                    "Total Trades": total_trades,
                    "Total Commissions [$]": round(total_commissions, 2),
                    "Net Return [%]": net_return,
                    "CAGR [%]": round(returns_analysis.get('cagr', 0) * 100, 2),
                    "Sharpe Ratio": round(sharpe_analysis.get('sharperatio', 0), 2),
                    "Max Profit [$]": round(max_profit, 2),
                    "Max Loss [$]": round(max_loss, 2)
                })

                # Salva trade details se presenti
                if stats.get('trades'):
                    trade_df = pd.DataFrame(stats['trades'])
                    trade_df["Stock"] = stock
                    trade_df["Strategy"] = strategy.__name__
                    all_trades.append(trade_df)

                print(f"📊 {stock} - {strategy.__name__}: Win Rate {results[-1]['Win Rate']}% | Net Return {net_return}%")

            except Exception as e:
                print(f"❌ Errore nella strategia {strategy.__name__} su {stock}: {e}")

    except Exception as e:
        print(f"❌ Errore dati per {stock}: {e}")

    return results, all_trades


# Esegui il backtest su tutti gli stock
if not filtered_stocks:
    print("❌ Nessun ticker soddisfa i criteri di selezione.")
else:
    all_results = []
    all_trades_data = []
    for stock in filtered_stocks:
        print(f'🔍 Analizzando stock: {stock}')
        results, trades = run_backtest_for_stock(stock, strategies)
        all_results.extend(results)
        all_trades_data.extend(trades)

    if all_results:
        results_df = pd.DataFrame(all_results, columns=RESULT_COLUMNS)
        if results_df.empty:
            print("⚠️ Il DataFrame è vuoto, non verrà salvato nessun file!")
        else:
            results_df.to_csv(REPORT_FILEPATH, index=False)
            print(f"✅ Risultati salvati in: {REPORT_FILEPATH}")
    else:
        print("❌ Nessun dato da salvare.")

    if all_trades_data:
        trades_df = pd.concat(all_trades_data, ignore_index=True)
        trades_df.to_csv(CSV_BACKTEST, index=False)
        print(f"✅ Dettagli dei trade salvati in: {CSV_BACKTEST}")
    else:
        print("⚠️ Nessun dettaglio trade da salvare.")

