import time
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

log = Logger("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/sma_cross_combined.log")

ib_manager = IBOrderManager()

# Strategy Parameters
ENTRY_START_TIME = time(16, 35)
ENTRY_END_TIME = time(16, 55)
EXIT_TIME = time(20, 50)
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SMA_TREND_PERIOD = 50
SL_PERCENT = 0.007
TP_PERCENT = 0.014
REDUCT_TP_PERCENT = 0.01
FIXED_CAPITAL = 1000

open_positions = {}
MAX_DAILY_TRADES = 5  # Numero massimo di posizioni aperte giornalmente
daily_trade_count = 0  # Contatore di trade giornalieri

def check_signals(df, stock):
    """Analyze SMA crossovers and return a BUY/SELL signal considering multiple filters."""
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

        log.log(f"SMA5: {sma1}, SMA20: {sma2}, SMA50: {sma50} | Previous SMA5: {prev_sma1}, SMA20: {prev_sma2}",
                stock=stock)

        if trade_confirmed:
            if sma1 > sma2 and prev_sma1 <= prev_sma2:
                entry_price = prev_candle_close + 0.02
                stop_loss = entry_price - (SL_PERCENT * entry_price)
                take_profit = entry_price + (TP_PERCENT * entry_price)
                log.log(f"BUY signal detected at {entry_price}, SL: {stop_loss}, TP: {take_profit}", stock=stock,
                        level="info")
                return ('BUY', entry_price, stop_loss, take_profit)

            elif sma1 < sma2 and prev_sma1 >= prev_sma2:
                entry_price = prev_candle_close - 0.02
                stop_loss = entry_price + (SL_PERCENT * entry_price)
                take_profit = entry_price - (TP_PERCENT * entry_price)
                log.log(f"SELL signal detected at {entry_price}, SL: {stop_loss}, TP: {take_profit}", stock=stock,
                        level="info")
                return ('SELL', entry_price, stop_loss, take_profit)

        log.log("No signal detected", stock=stock, level="debug")
        return None
    except Exception as e:
        log.log(f"Error calculating SMA: {e}", stock=stock, level="error")
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
            start_time = time.time()
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
                            signal = check_signals(df, ticker)

                            if signal and ticker not in open_positions:
                                action, entry_price, stop_loss, take_profit = signal
                                last_price = df['close'].iloc[-1]
                                quantity = int(FIXED_CAPITAL / last_price)

                                # 🔹 Usa ordine a LIMITE con il prezzo modificato
                                order_id = ib_manager.place_order(
                                    contract,
                                    action=action,
                                    quantity=quantity,
                                    order_type="limit",
                                    limit_price=entry_price  # Prezzo 2 cent sopra/sotto
                                )

                                if order_id:
                                    new_orders.append((order_id, contract))

                    ib_manager.update_orders(sl_percent=SL_PERCENT, tp_percent=TP_PERCENT)

            execution_time = time.time() - start_time
            sleep_time = max(0, 300 - execution_time)  # Assicura che il valore non sia negativo
            time.sleep(sleep_time)

    except Exception as e:
        log.log(f"❌ Error in trading loop: {e}", level="error")
        time.sleep(5)


def wait_for_precise_time(target_time=ENTRY_START_TIME):
    now = datetime.now()
    target_datetime = now.replace(hour=target_time.hour, minute=target_time.minute, second=1, microsecond=0)
    if now > target_datetime:
        target_datetime += timedelta(days=1)

    wait_seconds = (target_datetime - now).total_seconds()
    log.log(f"Wait {wait_seconds:.2f} seconds to start at {target_time},", level="info")
    time.sleep(wait_seconds)


if __name__ == "__main__":
    wait_for_precise_time()
    trading_loop()
