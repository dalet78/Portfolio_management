import time as tm
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list, get_all_check_functions, strategies_stock_applied
from support.logger import Logger
from libs.ibs_menager import IBOrderManager
from Trading.strategies_order.ema_crossing_trading_strategies.ema_cros_ema50_trading import check_ema_cross_ema50
from Trading.strategies_order.ema_crossing_trading_strategies.ema_cros_candle_trading import check_ema_cross_candle
from Trading.strategies_order.sma_crossing_trading_strategies.sma_cros_sma50_trading import check_sma_cross_sma50
from Trading.strategies_order.sma_crossing_trading_strategies.sma_cros_candle_trading import check_sma_cross_candle


log = Logger("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/sma_cross_candle.log")

ib_manager = IBOrderManager()

# Strategy Parameters
ENTRY_START_TIME = time(15, 35)
ENTRY_END_TIME = time(15, 50)
EXIT_TIME = time(19, 50)
SL_PERCENT = 0.007
TP_PERCENT = 0.014
REDUCT_TP_PERCENT = 0.01
FIXED_CAPITAL = 5000

open_positions = {}  # Memorizza le posizioni aperte
trade_count_per_stock = {}  # Memorizza il numero di trade per ciascun titolo
MAX_DAILY_TRADES = 5  # Numero massimo di posizioni aperte giornalmente
MAX_TRADES_PER_STOCK = 1


def trading_loop():
    start_time = tm.time()
    strategy_list = get_all_check_functions()
    current_time = datetime.now().time()

    for check_function_name in strategy_list:
        # Trova la strategia corrispondente nel dizionario
        strategy_name = None
        tickers_list = []
        strat_start_time = None
        strat_stop_time = None

        for strat_name, strat_data in strategies_stock_applied.items():
            if strat_data["check_function"] == check_function_name:
                strategy_name = strat_name
                tickers_list = strat_data["tickers"]
                strat_start_time = strat_data["start_time"]
                strat_stop_time = strat_data["stop_time"]
                break

        if not strategy_name:
            log.log(f"⚠️ Strategy not found for check function: {check_function_name}", level="warning")
            continue

        # Verifica se siamo nell'intervallo di tempo desiderato
        if not (strat_start_time <= current_time <= strat_stop_time):
            log.log(
                f"⏰ Strategy '{strategy_name}' non eseguita perché fuori dall'intervallo di tempo: {strat_start_time} - {strat_stop_time}",
                level="info")
            continue

        check_signals = globals().get(check_function_name)
        if check_signals is None:
            log.log(f"❌ Funzione non trovata: {check_function_name}", level="error")
            continue

        log.log(f"🔄 Starting trading loop for strategy: {strategy_name}", level="info")
        print(f"\n🔄 Strategy: {strategy_name}")
        print(f"📈 Stocks to trade: {tickers_list}")

        run_single_trading_iteration(strategy_name, tickers_list, check_signals)

    # ✅ Eseguito una sola volta alla fine
    log.log("📊 Aggiornamento ordini con SL/TP", level="info")
    ib_manager.update_orders(sl_percent=SL_PERCENT, tp_percent=TP_PERCENT)

    # ✅ Calcola durata e attende il tempo rimanente per arrivare a 5 minuti
    execution_time = tm.time() - start_time
    sleep_time = 300 - execution_time
    if sleep_time > 0:
        log.log(f"⏳ Sleeping for {sleep_time:.2f} secondi prima del prossimo ciclo", level="info")
        tm.sleep(sleep_time)
    else:
        log.log(f"⚠️ Nessun tempo di attesa, esecuzione durata {execution_time:.2f} secondi", level="warning")

def run_single_trading_iteration(strategy_name, tickers_list, check_signals):
    """Esegue una singola iterazione del ciclo di trading per una strategia."""
    try:
        new_orders = []
        for ticker in tickers_list:
            df, contract = ib_manager.get_stock_data(ticker)
            if df is not None:
                signal = check_signals(df, ticker)
                log.log(f"🔍 Segnale per {ticker}: {signal}", stock=ticker, level="debug")

                if not signal:
                    log.log(f"ℹ️ Nessun segnale valido per {ticker}", stock=ticker, level="info")
                    continue

                if ticker in open_positions:
                    log.log(f"⛔ {ticker} già in posizione aperta, salto ordine", stock=ticker, level="info")
                    continue

                last_price = df['close'].iloc[-1]
                quantity = int(FIXED_CAPITAL / last_price)

                if signal not in ["BUY", "SELL"]:
                    log.log(f"❌ Errore: Segnale non valido per {ticker}: {signal}", stock=ticker, level="error")
                else:
                    order_id = ib_manager.place_order(ticker, signal, quantity)
                    if order_id:
                        new_orders.append((order_id, contract))
                        log.log(f"✅ Ordine {signal} per {ticker} piazzato con ID {order_id}", stock=ticker, level="info")
                    else:
                        log.log(f"⚠️ Ordine per {ticker} fallito", stock=ticker, level="warning")

    except Exception as e:
        log.log(f"❌ Error in trading iteration for {strategy_name}: {e}", level="error")

def wait_for_precise_time(target_time=ENTRY_START_TIME):
    """Attende fino all'orario specificato."""
    now = datetime.now()

    # Assicurati che `target_time` sia un oggetto datetime.time
    if isinstance(target_time, datetime):
        target_time = tm.time()  # Converti in datetm.time

    target_datetime = now.replace(hour=target_time.hour, minute=target_time.minute, second=1, microsecond=0)

    if now > target_datetime:
        target_datetime += timedelta(days=1)  # Se l'orario è già passato oggi, impostalo per domani

    wait_seconds = (target_datetime - now).total_seconds()

    log.log(f"Wait {wait_seconds:.2f} seconds to start at {target_time}.", level="info")

    if wait_seconds > 0:
        tm.sleep(wait_seconds)  # ✅ Ora è un numero corretto

    log.log("Target time reached. Starting execution.", level="info")

if __name__ == "__main__":
    wait_for_precise_time()

    while True:
        trading_loop()  # Esegue tutte le strategie