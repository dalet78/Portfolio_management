SL_PERCENT = 0.007
TP_PERCENT = 0.014

def check_vwap_diff_signal(df, stock, log, trade_tracker):
    """Check for VWAP reversal signals and return a structured BUY/SELL signal."""
    log.log(f"Analyzing VWAP reversal signal for {stock}", stock=stock)

    try:
        df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

        # Verifica se ci sono abbastanza dati
        if len(df) < 1 or 'VWAP' not in df.columns:
            log.log("❌ VWAP not available or insufficient data", stock=stock, level="error")
            return {"signal": None, "reason": "no_vwap_data"}

        last = df.iloc[-1]
        candle_close = last['close']
        candle_high = last['high']
        candle_low = last['low']
        vwap_now = last['VWAP']

        log.log(f"Close: {candle_close} | Low: {candle_low} | High: {candle_high} | VWAP: {vwap_now}", stock=stock)

        # Long condition
        if (vwap_now - candle_low) / vwap_now >= 0.014:
            sl = candle_low - (SL_PERCENT * candle_low)
            tp = vwap_now
            entry = candle_close

            log.log(f"✅ BUY signal at {entry}, SL: {sl}, TP: {tp}", stock=stock, level="info")

            return {
                "signal": "BUY",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "market",
                "indicator": "VWAP",
                "reason": "vwap_reversal_long"
            }

        # Short condition
        elif (candle_high - vwap_now) / vwap_now >= 0.014:
            sl = candle_high + (SL_PERCENT * candle_high)
            tp = vwap_now
            entry = candle_close

            log.log(f"✅ SELL signal at {entry}, SL: {sl}, TP: {tp}", stock=stock, level="info")

            return {
                "signal": "SELL",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "market",
                "indicator": "VWAP",
                "reason": "vwap_reversal_short"
            }

        log.log("No VWAP signal detected", stock=stock, level="debug")
        return {"signal": None, "reason": "no_vwap_match"}

    except Exception as e:
        log.log(f"❌ Error calculating VWAP signal: {e}", stock=stock, level="error")
        return {"signal": None, "reason": f"error: {e}"}
