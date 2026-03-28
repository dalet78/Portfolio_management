import time as tm
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

# Strategy Parameters
SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SL_PERCENT = 0.007
TP_PERCENT = 0.014

def check_sma_cross_cents(df, stock, log, trade_tracker):
    """Analyze SMA crossovers and return a BUY/SELL signal with 2 cents entry adjustment."""
    log.log(f"Analyzing SMA signals for {stock}", stock=stock)

    try:
        df['SMA5'] = df['close'].rolling(SMA_SHORT_PERIOD).mean()
        df['SMA20'] = df['close'].rolling(SMA_LONG_PERIOD).mean()

        sma1, sma2 = df['SMA5'].iloc[-1], df['SMA20'].iloc[-1]
        prev_sma1, prev_sma2 = df['SMA5'].iloc[-2], df['SMA20'].iloc[-2]
        prev_candle_close = df['close'].iloc[-2]

        log.log(f"SMA5: {sma1}, SMA20: {sma2} | Prev SMA5: {prev_sma1}, SMA20: {prev_sma2}", stock=stock)

        # Bullish crossover
        if sma1 > sma2 and prev_sma1 <= prev_sma2:
            entry = prev_candle_close + 0.02
            sl = entry - (SL_PERCENT * entry)
            tp = entry + (TP_PERCENT * entry)

            log.log(f"✅ BUY signal at {entry}, (SL: {sl}, TP: {tp} will be calculated externally)", stock=stock, level="info")

            return {
                "signal": "BUY",
                "entry_price": entry,
                "sl": None,
                "tp": None,
                "order_type": "market",
                "indicator": "SMA",
                "reason": "sma_bullish_crossover_cents"
            }

        # Bearish crossover
        elif sma1 < sma2 and prev_sma1 >= prev_sma2:
            entry = prev_candle_close - 0.02
            sl = entry + (SL_PERCENT * entry)
            tp = entry - (TP_PERCENT * entry)

            log.log(f"✅ SELL signal at {entry}, (SL: {sl}, TP: {tp} will be calculated externally)", stock=stock, level="info")

            return {
                "signal": "SELL",
                "entry_price": entry,
                "sl": None,
                "tp": None,
                "order_type": "market",
                "indicator": "SMA",
                "reason": "sma_bearish_crossover_cents"
            }

        log.log("No signal detected", stock=stock, level="debug")
        return {"signal": None, "reason": "no_crossover"}

    except Exception as e:
        log.log(f"❌ Error calculating SMA: {e}", stock=stock, level="error")
        return {"signal": None, "reason": f"error: {e}"}
