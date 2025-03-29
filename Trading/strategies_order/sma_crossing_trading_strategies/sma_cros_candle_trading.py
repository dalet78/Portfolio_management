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

def check_sma_cross_candle(df, stock, log, trade_tracker):
    """Analyze SMA crossovers and return a BUY/SELL signal with candle confirmation."""
    log.log(f"Analyzing SMA signals for {stock}", stock=stock)

    try:
        df['SMA5'] = df['close'].rolling(SMA_SHORT_PERIOD).mean()
        df['SMA20'] = df['close'].rolling(SMA_LONG_PERIOD).mean()

        sma1, sma2 = df['SMA5'].iloc[-1], df['SMA20'].iloc[-1]
        prev_sma1, prev_sma2 = df['SMA5'].iloc[-2], df['SMA20'].iloc[-2]
        candle_close = df['close'].iloc[-1]
        candle_open = df['open'].iloc[-1]

        candle_direction = 'bullish' if candle_close > candle_open else 'bearish'

        log.log(
            f"SMA5: {sma1}, SMA20: {sma2} | Prev SMA5: {prev_sma1}, SMA20: {prev_sma2} | Candle direction: {candle_direction}",
            stock=stock
        )

        # Bullish crossover + bullish candle
        if sma1 > sma2 and prev_sma1 <= prev_sma2 and candle_direction == 'bullish':
            entry = candle_close
            sl = entry - (SL_PERCENT * entry)
            tp = entry + (TP_PERCENT * entry)

            log.log(f"✅ BUY signal at {entry}, SL: {sl}, TP: {tp}", stock=stock, level="info")

            return {
                "signal": "BUY",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "market",
                "indicator": "SMA",
                "reason": "sma_bullish_crossover_with_candle"
            }

        # Bearish crossover + bearish candle
        elif sma1 < sma2 and prev_sma1 >= prev_sma2 and candle_direction == 'bearish':
            entry = candle_close
            sl = entry + (SL_PERCENT * entry)
            tp = entry - (TP_PERCENT * entry)

            log.log(f"✅ SELL signal at {entry}, SL: {sl}, TP: {tp}", stock=stock, level="info")

            return {
                "signal": "SELL",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "market",
                "indicator": "SMA",
                "reason": "sma_bearish_crossover_with_candle"
            }

        log.log("No signal detected", stock=stock, level="debug")
        return {"signal": None, "reason": "no_crossover"}

    except Exception as e:
        log.log(f"❌ Error calculating SMA: {e}", stock=stock, level="error")
        return {"signal": None, "reason": f"error: {e}"}
