import time as tm
import numpy as np
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

log = Logger("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/sma_cross_candle.log")

ib_manager = IBOrderManager()

# Strategy Parameters
ENTRY_START_TIME = time(17, 0)
ENTRY_END_TIME = time(18, 0)
EXIT_TIME = time(19, 50)
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SL_PERCENT = 0.007
TP_PERCENT = 0.014
ATR_MULTIPLIER = 1.5  # 🔹 Evita trade su bassa volatilità
RSI_LONG_THRESHOLD = 55  # 🔹 RSI sopra questo livello per LONG
RSI_SHORT_THRESHOLD = 45  # 🔹 RSI sotto questo livello per SHORT
VOLUME_THRESHOLD = 0.7  # 🔹 Evita trade su bassi volumi (70% della media)
REDUCT_TP_PERCENT = 0.01
FIXED_CAPITAL = 5000

open_positions = {}  # Memorizza le posizioni aperte
trade_count_per_stock = {}  # Memorizza il numero di trade per ciascun titolo
MAX_DAILY_TRADES = 5  # Numero massimo di posizioni aperte giornalmente
MAX_TRADES_PER_STOCK = 1  # Limita gli ingressi per ogni titolo

def check_signals(df, stock):
    """Analyze VWAP breakout strategy with ATR, RSI, and volume filters."""
    log.log(f"Analyzing VWAP signals for {stock}", stock=stock)

    try:
        # Calcola gli indicatori richiesti
        df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        df['ATR'] = np.convolve((df['high'] - df['low']).rolling(14).mean(), np.ones(14) / 14, mode='same')
        df['RSI'] = np.convolve((df['close'].diff().clip(lower=0).rolling(14).mean() /
                                df['close'].diff().clip(upper=0).abs().rolling(14).mean()).fillna(0),
                                np.ones(14) / 14, mode='same') * 100
        df['VolumeAvg'] = df['volume'].rolling(20).mean()

        # Se non abbiamo abbastanza dati, usciamo
        if len(df) < 20:
            return None

        # Prezzi della candela precedente e attuale
        prev_candle_high = df['high'].iloc[-2]
        prev_candle_low = df['low'].iloc[-2]
        prev_candle_close = df['close'].iloc[-2]
        vwap = df['VWAP'].iloc[-1]
        atr = df['ATR'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        volume = df['volume'].iloc[-1]
        avg_volume = df['VolumeAvg'].iloc[-1]
        current_price = df['close'].iloc[-1]

        # Filtri di protezione
        if stock in open_positions:
            log.log(f"❌ Signal ignored: {stock} already has an open position.", stock=stock, level="debug")
            return None

        if stock not in trade_count_per_stock:
            trade_count_per_stock[stock] = 0

        if trade_count_per_stock[stock] >= MAX_TRADES_PER_STOCK:
            log.log(f"⚠️ Max trades reached for {stock}. Skipping signal.", stock=stock, level="debug")
            return None

        # **Filtro ATR: Minima volatilità**
        if abs(prev_candle_high - prev_candle_low) < ATR_MULTIPLIER * atr:
            log.log("⚠️ Skip trade: Volatilità troppo bassa (ATR Filter)", stock=stock, level="debug")
            return None

        # **Filtro VWAP Breakout Confirmation**
        if prev_candle_close < vwap and prev_candle_high > vwap:
            log.log("⚠️ Skip trade: Il prezzo non ha confermato il breakout su VWAP", stock=stock, level="debug")
            return None

        # **Filtro RSI: conferma trend**
        if rsi < RSI_LONG_THRESHOLD and rsi > RSI_SHORT_THRESHOLD:
            log.log("⚠️ Skip trade: RSI neutrale, nessuna conferma di trend forte", stock=stock, level="debug")
            return None

        # **Filtro di volume: Evitiamo trade in momenti di bassa liquidità**
        if volume < avg_volume * VOLUME_THRESHOLD:
            log.log("⚠️ Skip trade: Volume troppo basso rispetto alla media", stock=stock, level="debug")
            return None

        # **Condizioni per LONG**
        if prev_candle_high > vwap:
            entry_price = current_price
            stop_loss = entry_price * (1 - SL_PERCENT)
            take_profit = entry_price * (1 + TP_PERCENT)

            if stop_loss < entry_price < take_profit:
                log.log(f"✅ BUY signal detected at {entry_price}, SL: {stop_loss}, TP: {take_profit}", stock=stock, level="info")
                open_positions[stock] = {"type": "BUY", "entry": entry_price, "sl": stop_loss, "tp": take_profit}
                trade_count_per_stock[stock] += 1
                return 'BUY'

        # **Condizioni per SHORT**
        if prev_candle_low < vwap:
            entry_price = current_price
            stop_loss = entry_price * (1 + SL_PERCENT)
            take_profit = entry_price * (1 - TP_PERCENT)

            if stop_loss > entry_price > take_profit:
                log.log(f"✅ SELL signal detected at {entry_price}, SL: {stop_loss}, TP: {take_profit}", stock=stock, level="info")
                open_positions[stock] = {"type": "SELL", "entry": entry_price, "sl": stop_loss, "tp": take_profit}
                trade_count_per_stock[stock] += 1
                return 'SELL'

        log.log("No signal detected", stock=stock, level="debug")
        return None

    except Exception as e:
        log.log(f"❌ Error calculating VWAP strategy: {e}", stock=stock, level="error")
        return None



def trading_loop():
    """Main trading loop that handles signals and orders."""

    now = datetime.now().time()
    log.log("Starting trading loop", level="info")
    tickers_list = get_stock_list("vwap_pivot_breackout")
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
                            signal = check_signals(df, ticker)
                            if signal and ticker not in open_positions:
                                last_price = df['close'].iloc[-1]
                                quantity = int(FIXED_CAPITAL / last_price)

                                # ✅ Verifica che action sia 'BUY' o 'SELL' prima di passarlo a place_order
                                if signal not in ["BUY", "SELL"]:
                                    log.log(f"❌ Errore: Segnale non valido per {ticker}: {signal}", stock=ticker,
                                            level="error")
                                else:
                                    order_id = ib_manager.place_order(ticker, signal, quantity)
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
    trading_loop()
