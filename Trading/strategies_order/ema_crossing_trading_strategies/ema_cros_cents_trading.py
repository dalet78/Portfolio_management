import time as tm
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

log = Logger("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/ema_cross_cents.log")

ib_manager = IBOrderManager()

# Strategy Parameters
ENTRY_START_TIME = time(15, 35)
ENTRY_END_TIME = time(15, 50)
EXIT_TIME = time(19, 50)
EMA_SHORT_PERIOD = 9
EMA_LONG_PERIOD = 21
SL_PERCENT = 0.007
TP_PERCENT = 0.014
REDUCT_TP_PERCENT = 0.01
FIXED_CAPITAL = 5000

open_positions = {}  # Memorizza le posizioni aperte
trade_count_per_stock = {}  # Memorizza il numero di trade per ciascun titolo
MAX_DAILY_TRADES = 5  # Numero massimo di posizioni aperte giornalmente
MAX_TRADES_PER_STOCK = 1  # Limita gli ingressi per ogni titolo


def EMA_Cross_cents(df, stock):
    """Analyze EMA crossovers and return a BUY/SELL signal considering fixed entry adjustments."""
    log.log(f"Analyzing EMA signals for {stock}", stock=stock)

    try:
        df['EMA9'] = df['close'].ewm(span=EMA_SHORT_PERIOD, adjust=False).mean()
        df['EMA21'] = df['close'].ewm(span=EMA_LONG_PERIOD, adjust=False).mean()

        ema1, ema2 = df['EMA9'].iloc[-1], df['EMA21'].iloc[-1]  # EMA sulla candela attuale
        prev_ema1, prev_ema2 = df['EMA9'].iloc[-2], df['EMA21'].iloc[-2]
        prev_candle_close = df['close'].iloc[-2]

        log.log(f"EMA9: {ema1}, EMA21: {ema2} | Previous EMA9: {prev_ema1}, EMA21: {prev_ema2}", stock=stock)

        # Verifica se il titolo ha già una posizione aperta
        if stock in open_positions:
            log.log(f"❌ Signal ignored: {stock} already has an open position.", stock=stock, level="debug")
            return None

        # Conta il numero di operazioni già eseguite su questo titolo
        if stock not in trade_count_per_stock:
            trade_count_per_stock[stock] = 0

        if trade_count_per_stock[stock] >= MAX_TRADES_PER_STOCK:
            log.log(f"⚠️ Max trades reached for {stock}. Skipping signal.", stock=stock, level="debug")
            return None

        if ema1 > ema2 and prev_ema1 <= prev_ema2:
            entry_price = prev_candle_close + 0.02
            stop_loss = entry_price - (SL_PERCENT * entry_price)
            take_profit = entry_price + (TP_PERCENT * entry_price)

            log.log(f"✅ BUY signal detected at {entry_price}, SL: {stop_loss}, TP: {take_profit}", stock=stock,
                    level="info")

            # Registra l'operazione aperta
            open_positions[stock] = {"type": "BUY", "entry": entry_price, "sl": stop_loss, "tp": take_profit}
            trade_count_per_stock[stock] += 1
            return 'BUY', entry_price

        elif ema1 < ema2 and prev_ema1 >= prev_ema2:
            entry_price = prev_candle_close - 0.02
            stop_loss = entry_price + (SL_PERCENT * entry_price)
            take_profit = entry_price - (TP_PERCENT * entry_price)

            log.log(f"✅ SELL signal detected at {entry_price}, SL: {stop_loss}, TP: {take_profit}", stock=stock,
                    level="info")

            # Registra l'operazione aperta
            open_positions[stock] = {"type": "SELL", "entry": entry_price, "sl": stop_loss, "tp": take_profit}
            trade_count_per_stock[stock] += 1
            return 'SELL', entry_price

        log.log("No signal detected", stock=stock, level="debug")
        return None
    except Exception as e:
        log.log(f"❌ Error calculating EMA: {e}", stock=stock, level="error")
        return None

#
# def trading_loop():
#     """Main trading loop that handles signals and orders."""
#
#     now = datetime.now().time()
#     log.log("Starting trading loop", level="info")
#     tickers_list = get_stock_list("EMA_Cross_cents")
#     log.log(f"Stocks to trade: {tickers_list}", level="info")
#     print(f"Stocks to trade: {tickers_list}")
#
#     try:
#         while True:
#             start_time = tm.time()
#             now = datetime.now().time()
#             if now >= EXIT_TIME:
#                 log.log("Exit time reached, closing open positions", level="info")
#                 for pos in ib_manager.ib.positions():
#                     print(f"🔹 Chiudendo {pos.position} azioni di {pos.contract.symbol}")
#                     ib_manager.close_position(pos.contract)
#             else:
#                 if ENTRY_START_TIME <= now <= ENTRY_END_TIME:
#                     new_orders = []  # Lista per tracciare nuovi ordini
#                     for ticker in tickers_list:
#                         df, contract = ib_manager.get_stock_data(ticker)
#                         if df is not None:
#                             signal, entry_price = check_signals(df, ticker)
#                             if signal and ticker not in open_positions:
#                                 last_price = df['close'].iloc[-1]
#                                 quantity = int(FIXED_CAPITAL / last_price)
#
#                                 # 🔹 Usa ordine a LIMITE con il prezzo modificato
#                                 order_id = ib_manager.place_order(
#                                     ticker,
#                                     action=signal,  # ✅ Ora action è definito
#                                     quantity=quantity,
#                                     order_type="limit",
#                                     limit_price=entry_price  # ✅ Ora entry_price è definito
#                                 )
#
#                                 if order_id:
#                                     new_orders.append((order_id, contract))
#
#             execution_time = tm.time() - start_time
#             sleep_time = 300 - execution_time  # Ensure non-negative sleep time
#             tm.sleep(sleep_time)
#     except Exception as e:
#         log.log(f"❌ Error in trading loop: {e}", level="error")
#         tm.sleep(5)
#
#
# def wait_for_precise_time(target_time=ENTRY_START_TIME):
#     """Attende fino all'orario specificato."""
#     now = datetime.now()
#
#     # Assicurati che `target_time` sia un oggetto datetime.time
#     if isinstance(target_time, datetime):
#         target_time = tm.time()  # Converti in datetm.time
#
#     target_datetime = now.replace(hour=target_time.hour, minute=target_time.minute, second=1, microsecond=0)
#
#     if now > target_datetime:
#         target_datetime += timedelta(days=1)  # Se l'orario è già passato oggi, impostalo per domani
#
#     wait_seconds = (target_datetime - now).total_seconds()
#
#     log.log(f"Wait {wait_seconds:.2f} seconds to start at {target_time}.", level="info")
#
#     if wait_seconds > 0:
#         tm.sleep(wait_seconds)  # ✅ Ora è un numero corretto
#
#     log.log("Target time reached. Starting execution.", level="info")
#
#
# if __name__ == "__main__":
#     wait_for_precise_time()
#     trading_loop()
