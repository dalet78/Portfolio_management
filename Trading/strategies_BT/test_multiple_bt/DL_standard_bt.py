import os
import pandas as pd
from backtesting import Backtest
from libs.filtered_stock import return_filtred_list
from support.data_preparation import DataRefactory
# from Trading.strategies_BT.Breakout_Strategies_BT.nr7_filtred_breakout import NR7FiltredStrategy
from Trading.strategies_BT.sma_crossing.DL_starategies.DL_candel_filter import HOLC_DL_Strategy_Candle
from libs.technical_indicators.volume_indicators import VolumeIndicators
from libs.technical_indicators.trends_indicators import TrendIndicators
from libs.technical_indicators.momentum_indicators import MomentumIndicators
from libs.technical_indicators.volatility_indicators import VolatilityIndicators


# Costanti
DATA_DIRECTORY = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
ALL_DATA_PATH = f"{DATA_DIRECTORY}/Data/ALL/5min"
REPORT_DIRECTORY = f"{DATA_DIRECTORY}/Reports/Data"
REPORT_FILEPATH = f"{REPORT_DIRECTORY}/backtest_sma_cross_with_joblib.csv"
COMMISSION_PER_TRADE = 2  # Commissione fissa per operazione
RESULT_COLUMNS = ["Stock", "Strategy", "Win Rate", "Max Drawdown", "Return [%]",
                  "Total Trades", "Total Commissions [$]", "Net Return [%]", "CAGR [%]", "Sharpe Ratio"]

# Creazione della directory dei report se non esiste
os.makedirs(REPORT_DIRECTORY, exist_ok=True)

# Lista degli stock e strategie da testare
filtered_stocks = return_filtred_list(index="ALL")
strategies = [HOLC_DL_Strategy_Candle]


def run_backtest_for_stock(stock, strategies):
    """Esegui il backtest per un singolo stock con le strategie specificate e raccogli i risultati."""
    results = []
    try:
        data_filepath = f"{ALL_DATA_PATH}/{stock}_historical_data.csv"
        if not os.path.exists(data_filepath):
            print(f"⚠️ File non trovato: {data_filepath}")
            return results

        df = DataRefactory.prepare_min_csv(filepath=data_filepath)
        df = add_essential_indicators(df)
        # df = DataRefactory.convert_5m_to_15m(df)
        # Controlla tipo di indice
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError(f"Indice non è DatetimeIndex per {data_filepath}")

        # Nessun NaT
        if df.index.isnull().any():
            raise ValueError(f"Indice contiene valori nulli per {data_filepath}")

        # Debug stampa tipo index
        print("🕒 Tipo indice:", type(df.index), "Frequenza stimata:", pd.infer_freq(df.index))

        for strategy in strategies:
            try:
                bt = Backtest(df, strategy, cash=10000, exclusive_orders=True)
                stats = bt.run()
                print(stats)

                # Numero totale di operazioni
                total_trades = int(stats['_trades'].shape[0]) if stats['_trades'] is not None else 0

                # Calcolo delle commissioni totali
                total_commissions = total_trades * COMMISSION_PER_TRADE

                # Calcolo del Return Netto dopo le commissioni
                gross_return = stats.get('Return [%]', 0)  # Rendimento lordo
                net_return = round(gross_return - (total_commissions / 10000 * 100), 2)  # Netto

                # Arrotondamento dei valori a due cifre decimali
                results.append({
                    "Stock": stock,
                    "Strategy": strategy.__name__,
                    "Win Rate": round(stats.get('Win Rate [%]', 0), 2),
                    "Max Drawdown": round(stats.get('Max. Drawdown [%]', 0), 2),
                    "Return [%]": round(gross_return, 2),
                    "Total Trades": total_trades,
                    "Total Commissions [$]": round(total_commissions, 2),
                    "Net Return [%]": net_return,
                    "CAGR [%]": round(stats.get('CAGR [%]', 0), 2),
                    "Sharpe Ratio": round(stats.get('Sharpe Ratio', 0), 2)
                })

                print(
                    f'✅ {stock} - {strategy.__name__}: Win Rate {round(stats.get("Win Rate [%]", 0), 2)}% | Net Return: {net_return}%')

            except Exception as e:
                print(f"❌ Errore durante il backtest di {stock} con {strategy.__name__}: {e}")

    except Exception as e:
        print(f"❌ Errore durante l'elaborazione di {stock}: {e}")

    return results

def add_essential_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = TrendIndicators(df).sma(5).sma(20).result
    df = VolumeIndicators(df).vwap().result
    df = MomentumIndicators(df).rsi(14).result
    df = VolatilityIndicators(df).atr(14).result

    df['sma_ratio'] = df['SMA_5'] / df['SMA_20']
    df['volume_ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
    df['gap'] = df['Open'] - df['Close'].shift(1)
    df['price_vs_vwap'] = df['Close'] - df['VWAP']

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df['day_of_week'] = df.index.dayofweek

    # Forza il tipo numerico per evitare problemi con LightGBM
    numerics = [
        'SMA_5', 'SMA_20', 'sma_ratio', 'volume_ratio', 'VWAP',
        'gap', 'RSI_14', 'ATR_14', 'price_vs_vwap', 'day_of_week'
    ]
    for col in numerics:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.dropna()


# Esegui il backtest su tutti gli stock
if not filtered_stocks:
    print("❌ Nessun ticker soddisfa i criteri di selezione.")
else:
    all_results = []
    for stock in filtered_stocks:
        print(f'🔍 Analizzando stock: {stock}')
        all_results.extend(run_backtest_for_stock(stock, strategies))

    # Salva i risultati se presenti
    if all_results:
        results_df = pd.DataFrame(all_results, columns=RESULT_COLUMNS)

        if results_df.empty:
            print("⚠️ Il DataFrame è vuoto, non verrà salvato nessun file!")
        else:
            results_df.to_csv(REPORT_FILEPATH, index=False)
            print(f"✅ Risultati salvati in: {REPORT_FILEPATH}")

    else:
        print("❌ Nessun dato da salvare.")
