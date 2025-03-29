import time as tm
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

SMA_SHORT_PERIOD = 5
SMA_LONG_PERIOD = 20
SMA_TREND_PERIOD = 50
SL_PERCENT = 0.007
TP_PERCENT = 0.014

def check_sma_cross_combined(df, stock, log, trade_tracker):
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

        candle_direction = "bullish" if prev_candle_close > prev_candle_open else "bearish"

        candle_filter_passed = (candle_direction == "bullish" and sma1 > sma2) or \
                               (candle_direction == "bearish" and sma1 < sma2)

        sma50_filter_passed = (sma1 > sma50 and sma1 > sma2) or \
                              (sma1 < sma50 and sma1 < sma2)

        trade_confirmed = candle_filter_passed or sma50_filter_passed

        log.log(
            f"SMA5: {sma1}, SMA20: {sma2}, SMA50: {sma50} | Prev SMA5: {prev_sma1}, SMA20: {prev_sma2} | "
            f"Direction: {candle_direction} | Confirmed: {trade_confirmed}",
            stock=stock)

        if not trade_confirmed:
            log.log("No signal detected", stock=stock, level="debug")
            return {"signal": None, "reason": "filters_not_passed"}

        # Crossover rialzista
        if sma1 > sma2 and prev_sma1 <= prev_sma2:
            entry = prev_candle_close + 0.02
            sl = entry - (SL_PERCENT * entry)
            tp = entry + (TP_PERCENT * entry)

            log.log(f"✅ BUY signal at {entry}, SL: {sl}, TP: {tp}", stock=stock, level="info")

            return {
                "signal": "BUY",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "limit",
                "indicator": "SMA",
                "reason": "sma_bullish_crossover_combined"
            }

        # Crossover ribassista
        elif sma1 < sma2 and prev_sma1 >= prev_sma2:
            entry = prev_candle_close - 0.02
            sl = entry + (SL_PERCENT * entry)
            tp = entry - (TP_PERCENT * entry)

            log.log(f"✅ SELL signal at {entry}, SL: {sl}, TP: {tp}", stock=stock, level="info")

            return {
                "signal": "SELL",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "limit",
                "indicator": "SMA",
                "reason": "sma_bearish_crossover_combined"
            }

        log.log("No signal after filters despite confirmation", stock=stock, level="debug")
        return {"signal": None, "reason": "no_crossover"}

    except Exception as e:
        log.log(f"❌ Error calculating SMA: {e}", stock=stock, level="error")
        return {"signal": None, "reason": f"error: {e}"}


