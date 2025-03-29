import time as tm
from datetime import datetime, time, timedelta
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

# Strategy Parameters
EMA_SHORT_PERIOD = 9
EMA_LONG_PERIOD = 21
EMA_TREND_PERIOD = 50
SL_PERCENT = 0.007
TP_PERCENT = 0.014

def check_ema_cross_ema50(df, stock, log, trade_tracker):
    """Analyze EMA crossovers and return a BUY/SELL signal with EMA50 trend filter."""
    log.log(f"Analyzing EMA signals for {stock}", stock=stock)

    try:
        df['EMA9'] = df['close'].ewm(span=EMA_SHORT_PERIOD, adjust=False).mean()
        df['EMA21'] = df['close'].ewm(span=EMA_LONG_PERIOD, adjust=False).mean()
        df['EMA50'] = df['close'].ewm(span=EMA_TREND_PERIOD, adjust=False).mean()

        ema1, ema2, ema50 = df['EMA9'].iloc[-2], df['EMA21'].iloc[-2], df['EMA50'].iloc[-2]
        prev_ema1, prev_ema2 = df['EMA9'].iloc[-3], df['EMA21'].iloc[-3]
        close_now = df['close'].iloc[-1]
        next_candle_open = df['open'].iloc[-1]

        log.log(f"EMA9: {ema1}, EMA21: {ema2}, EMA50: {ema50} | Prev EMA9: {prev_ema1}, EMA21: {prev_ema2}", stock=stock)

        # BUY setup: crossover EMA9 > EMA21 + trend sopra EMA50
        if ema1 > ema2 and prev_ema1 <= prev_ema2 and close_now > ema50:
            entry = next_candle_open
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
                "reason": "ema_bullish_trend_crossover"
            }

        # SELL setup: crossover EMA9 < EMA21 + trend sotto EMA50
        elif ema1 < ema2 and prev_ema1 >= prev_ema2 and close_now < ema50:
            entry = next_candle_open
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
                "reason": "ema_bearish_trend_crossover"
            }

        log.log("No signal detected", stock=stock, level="debug")
        return {"signal": None, "reason": "no_crossover"}

    except Exception as e:
        log.log(f"❌ Error calculating EMA: {e}", stock=stock, level="error")
        return {"signal": None, "reason": f"error: {e}"}
