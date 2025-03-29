import time as tm
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

# Strategy Parameters
EMA_SHORT_PERIOD = 9
EMA_LONG_PERIOD = 21
SL_PERCENT = 0.007
TP_PERCENT = 0.014

def check_ema_cross_candle(df, stock, log, trade_tracker):
    """Analyze EMA crossovers and return a BUY/SELL signal with candle confirmation."""
    log.log(f"Analyzing EMA signals for {stock}", stock=stock)

    try:
        df['EMA9'] = df['close'].ewm(span=EMA_SHORT_PERIOD, adjust=False).mean()
        df['EMA21'] = df['close'].ewm(span=EMA_LONG_PERIOD, adjust=False).mean()

        ema1, ema2 = df['EMA9'].iloc[-1], df['EMA21'].iloc[-1]
        prev_ema1, prev_ema2 = df['EMA9'].iloc[-2], df['EMA21'].iloc[-2]
        candle_close = df['close'].iloc[-1]
        candle_open = df['open'].iloc[-1]

        candle_direction = "bullish" if candle_close > candle_open else "bearish"

        log.log(
            f"EMA9: {ema1}, EMA21: {ema2} | Prev EMA9: {prev_ema1}, EMA21: {prev_ema2} | Candle: {candle_direction}",
            stock=stock
        )

        # BUY crossover + bullish candle
        if ema1 > ema2 and prev_ema1 <= prev_ema2 and candle_direction == "bullish":
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
                "indicator": "EMA",
                "reason": "ema_bullish_candle_confirmation"
            }

        # SELL crossover + bearish candle
        elif ema1 < ema2 and prev_ema1 >= prev_ema2 and candle_direction == "bearish":
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
                "indicator": "EMA",
                "reason": "ema_bearish_candle_confirmation"
            }

        log.log("No signal detected", stock=stock, level="debug")
        return {"signal": None, "reason": "no_crossover"}

    except Exception as e:
        log.log(f"❌ Error calculating EMA: {e}", stock=stock, level="error")
        return {"signal": None, "reason": f"error: {e}"}
