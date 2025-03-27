import time as tm
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

log = Logger("/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/sma_cross_candle.log")

ib_manager = IBOrderManager()
open_positions = {}  # Memorizza le posizioni aperte
trade_count_per_stock = {}  # Memorizza il numero di trade per ciascun titolo
MAX_DAILY_TRADES = 5  # Numero massimo di posizioni aperte giornalmente
MAX_TRADES_PER_STOCK = 1

def check_vwap_diff_signal(df, stock):
    """Verifica segnali VWAP reversal per ingresso BUY/SELL e restituisce il segnale."""
    log.log(f"Analyzing VWAP reversal signal for {stock}", stock=stock)
    df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

    try:
        # Verifica se ci sono abbastanza dati
        if len(df) < 1 or 'vwap' not in df.columns:
            log.log("❌ VWAP non disponibile o dati insufficienti", stock=stock, level="error")
            return None

        # Ultima candela
        last = df.iloc[-1]
        candle_close = last['close']
        candle_high = last['high']
        candle_low = last['low']
        vwap_now = last['VWAP']

        # Controlli di protezione
        if stock in open_positions:
            log.log(f"❌ Signal ignored: {stock} already has an open position.", stock=stock, level="debug")
            return None

        if stock not in trade_count_per_stock:
            trade_count_per_stock[stock] = 0

        if trade_count_per_stock[stock] >= MAX_TRADES_PER_STOCK:
            log.log(f"⚠️ Max trades reached for {stock}. Skipping signal.", stock=stock, level="debug")
            return None

        # Log info
        log.log(f"Close: {candle_close} | Low: {candle_low} | High: {candle_high} | VWAP: {vwap_now} | Direction: {candle_direction}", stock=stock)

        # Condizione LONG
        if (vwap_now - candle_low) / vwap_now >= 0.014:
            stop_loss = candle_low - (0.007 * candle_low)
            take_profit = vwap_now

            open_positions[stock] = {
                "type": "BUY",
                "entry": candle_close,
                "sl": stop_loss,
                "tp": take_profit
            }
            trade_count_per_stock[stock] += 1

            log.log(f"✅ BUY signal detected at {candle_close}, SL: {stop_loss}, TP: {take_profit}", stock=stock, level="info")
            return 'BUY'

        # Condizione SHORT
        elif (candle_high - vwap_now) / vwap_now >= 0.014:
            stop_loss = candle_close + (0.007 * candle_close)
            take_profit = vwap_now

            open_positions[stock] = {
                "type": "SELL",
                "entry": candle_close,
                "sl": stop_loss,
                "tp": take_profit
            }
            trade_count_per_stock[stock] += 1

            log.log(f"✅ SELL signal detected at {candle_close}, SL: {stop_loss}, TP: {take_profit}", stock=stock, level="info")
            return 'SELL'

        log.log("No VWAP signal detected", stock=stock, level="debug")
        return None

    except Exception as e:
        log.log(f"❌ Error calculating VWAP signal: {e}", stock=stock, level="error")
        return None
