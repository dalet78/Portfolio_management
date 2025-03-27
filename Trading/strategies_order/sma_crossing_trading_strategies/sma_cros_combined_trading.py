import time as tm
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

log = Logger("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/sma_cross_combined.log")

ib_manager = IBOrderManager()

# Strategy Parameters
ENTRY_START_TIME = time(15, 35)
ENTRY_END_TIME = time(15, 50)
EXIT_TIME = time(19, 50)
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SMA_TREND_PERIOD = 50
SL_PERCENT = 0.007
TP_PERCENT = 0.014
REDUCT_TP_PERCENT = 0.01
FIXED_CAPITAL = 5000

open_positions = {}  # Memorizza le posizioni aperte
trade_count_per_stock = {}  # Memorizza il numero di trade per ciascun titolo
MAX_DAILY_TRADES = 5  # Numero massimo di posizioni aperte giornalmente
MAX_TRADES_PER_STOCK = 1  # Limita gli ingressi per ogni titolo

def check_signals(df, stock):
    """Analyze SMA crossovers and return a BUY/SELL signal considering multiple filters with trade protections."""
    log.log(f"Analyzing SMA signals for {stock}", stock=stock)

    try:
        df['SMA5'] = df['close'].rolling(SMA_SHORT_PERIOD).mean()
        df['SMA20'] = df['close'].rolling(SMA_LONG_PERIOD).mean()
        df['SMA50'] = df['close'].rolling(SMA_TREND_PERIOD).mean()

        sma1, sma2, sma50 = df['SMA5'].iloc[-2], df['SMA20'].iloc[-2], df['SMA50'].iloc[-2]
        prev_sma1, prev_sma2 = df['SMA5'].iloc[-3], df['SMA20'].iloc[-3]
        prev_candle_close = df['close'].iloc[-2]
        prev_candle_open = df['open'].iloc[-2]
        next_candle_open = df['open'].iloc[-1]

        # Determina la direzione della candela
        candle_direction = "bullish" if prev_candle_close > prev_candle_open else "bearish"

        # **Filtro HOLCStrategy_Candle**: la candela deve confermare il trend
        candle_filter_passed = (candle_direction == "bullish" and sma1 > sma2) or \
                               (candle_direction == "bearish" and sma1 < sma2)

        # **Filtro HOLCStrategy_SMA50**: crossover deve avvenire sopra/sotto la SMA50
        sma50_filter_passed = (sma1 > sma50 and sma1 > sma2) or (sma1 < sma50 and sma1 < sma2)

        # **Conferma trade**: almeno uno dei due filtri deve essere attivo
        trade_confirmed = candle_filter_passed or sma50_filter_passed

        log.log(f"SMA5: {sma1}, SMA20: {sma2}, SMA50: {sma50} | Previous SMA5: {prev_sma1}, SMA20: {prev_sma2} | Trade Confirmed: {trade_confirmed}",
                stock=stock)

        # Protezioni contro ingressi multipli
        if stock in open_positions:
            log.log(f"❌ Signal ignored: {stock} already has an open position.", stock=stock, level="debug")
            return None

        if stock not in trade_count_per_stock:
            trade_count_per_stock[stock] = 0

        if trade_count_per_stock[stock] >= MAX_TRADES_PER_STOCK:
            log.log(f"⚠️ Max trades reached for {stock}. Skipping signal.", stock=stock, level="debug")
            return None

        if trade_confirmed:
            if sma1 > sma2 and prev_sma1 <= prev_sma2:
                entry_price = prev_candle_close + 0.02  # ENTRY a 2 cent sopra la chiusura della candela di crossover
                stop_loss = entry_price - (SL_PERCENT * entry_price)
                take_profit = entry_price + (TP_PERCENT * entry_price)

                log.log(f"✅ BUY signal detected at {entry_price}, SL: {stop_loss}, TP: {take_profit}", stock=stock, level="info")

                # Registra l'operazione aperta
                open_positions[stock] = {"type": "BUY", "entry": entry_price, "sl": stop_loss, "tp": take_profit}
                trade_count_per_stock[stock] += 1
                return 'BUY', entry_price

            elif sma1 < sma2 and prev_sma1 >= prev_sma2:
                entry_price = prev_candle_close - 0.02  # ENTRY a 2 cent sotto la chiusura della candela di crossover
                stop_loss = entry_price + (SL_PERCENT * entry_price)
                take_profit = entry_price - (TP_PERCENT * entry_price)

                log.log(f"✅ SELL signal detected at {entry_price}, SL: {stop_loss}, TP: {take_profit}", stock=stock, level="info")

                # Registra l'operazione aperta
                open_positions[stock] = {"type": "SELL", "entry": entry_price, "sl": stop_loss, "tp": take_profit}
                trade_count_per_stock[stock] += 1
                return 'SELL', entry_price

        log.log("No signal detected", stock=stock, level="debug")
        return None
    except Exception as e:
        log.log(f"❌ Error calculating SMA: {e}", stock=stock, level="error")
        return None




def trading_loop():
    """Main trading loop that handles signals and orders."""

    now = datetime.now().time()
    log.log("Starting trading loop", level="info")
    tickers_list = get_stock_list("SMA_Cross_combined")
    log.log(f"Stocks to trade: {tickers_list}", level="info")
    print(f"Stocks to trade: {tickers_list}")

    try:
        while True:
            start_time = tm.time()
            now = datetime.now().time()
            if now >= EXIT_TIME:
                log.log("Exit time reached, closing open positions", level="info")
                for pos in ib_manager.ib.positions():
                    print(f"🔹 Chiudendo {pos.position} azioni di {pos.contract.symbol}")
                    ib_manager.close_position(pos.contract)
            else:
                if ENTRY_START_TIME <= now <= ENTRY_END_TIME:
                    new_orders = []  # Lista per tracciare nuovi ordini
                    for ticker in tickers_list:
                        df, contract = ib_manager.get_stock_data(ticker)
                        if df is not None:
                            signal, entry_price = check_signals(df, ticker)
                            if signal and ticker not in open_positions:
                                last_price = df['close'].iloc[-1]
                                quantity = int(FIXED_CAPITAL / last_price)

                                # 🔹 Usa ordine a LIMITE con il prezzo modificato
                                order_id = ib_manager.place_order(
                                    ticker,
                                    action=signal,  # ✅ Ora action è definito
                                    quantity=quantity,
                                    order_type="limit",
                                    limit_price=entry_price  # ✅ Ora entry_price è definito
                                )

                                if order_id:
                                    new_orders.append((order_id, contract))

                    ib_manager.update_orders(sl_percent=SL_PERCENT, tp_percent=TP_PERCENT)

            execution_time = tm.time() - start_time
            sleep_time = 300 - execution_time  # Ensure non-negative sleep time
            tm.sleep(sleep_time)
    except Exception as e:
        log.log(f"❌ Error in trading loop: {e}", level="error")
        tm.sleep(5)


def wait_for_precise_time(target_time=ENTRY_START_TIME):
    """Attende fino all'orario specificato."""
    now = datetime.now()

    # Assicurati che `target_time` sia un oggetto datetime.time
    if isinstance(target_time, datetime):
        target_time = target_time.time()  # Converti in datetime.time

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
    trading_loop()
