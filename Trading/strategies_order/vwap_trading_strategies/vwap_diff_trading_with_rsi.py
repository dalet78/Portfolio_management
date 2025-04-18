import talib
import pandas as pd
from datetime import datetime

def check_vwap_diff_signal_with_rsi(df, stock, log, trade_tracker,
                           entry_threshold=0.014,
                           sl_percent=0.007,
                           reward_to_risk_ratio=2.0,
                           max_tp_ratio=0.05,
                           rsi_period=14,
                           rsi_oversold=30,
                           rsi_overbought=70):
    """Check for VWAP reversal signals with RSI filter."""

    log.log(f"Analyzing VWAP reversal signal for {stock}", stock=stock)

    try:
        if 'date_only' not in df.columns:
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df.set_index('date', inplace=True)
                else:
                    raise ValueError("❌ 'date' column is missing and index is not a DatetimeIndex.")
            df['date_only'] = df.index.date

        df['RSI'] = talib.RSI(df['close'], timeperiod=rsi_period)
        # Filtra per la data odierna
        today = datetime.now().date()
        df_today = df[df['date_only'] == today].copy()

        # Rimuovi 'date_only' dopo il filtraggio
        df_today.drop(columns=['date_only'], inplace=True)

        df_vwap = get_vwap(df_today)

        if df_vwap is None or df_vwap.empty:
            return {"signal": None, "reason": "no_current_day_data"}

        last = df_today.iloc[-1]
        entry = last['close']
        high = last['high']
        low = last['low']
        vwap = last['VWAP']
        rsi_val = last['RSI']

        if pd.isna(rsi_val):
            return {"signal": None, "reason": "rsi_not_available"}

        log.log(f"Close: {entry} | Low: {low} | High: {high} | VWAP: {vwap} | RSI: {rsi_val:.2f}", stock=stock)

        # Log delle differenze per l'ultima candela
        diff_low_pct = (vwap - low) / vwap * 100 if vwap != 0 else 0
        diff_high_pct = (high - vwap) / vwap * 100 if vwap != 0 else 0
        log.log(f"[{stock}] Last Candela: VWAP-Low={diff_low_pct:.2f}%, High-VWAP={diff_high_pct:.2f}%", stock=stock,
                level="debug")

        # 🟢 LONG
        if (vwap - low) / vwap >= entry_threshold and rsi_val <= rsi_oversold:
            sl = low - sl_percent * low
            risk = entry - sl
            tp = entry + reward_to_risk_ratio * risk

            if abs(tp - entry) / entry > max_tp_ratio:
                log.log(f"⚠️ TP too far for BUY: {tp:.2f} (>{max_tp_ratio * 100:.1f}%)", stock=stock)
                return {"signal": None, "reason": "tp_too_far_long"}

            log.log(f"✅ BUY signal | Entry: {entry:.2f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi_val:.2f}", stock=stock,
                    level="info")
            return {
                "signal": "BUY",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "market",
                "indicator": "VWAP+RSI",
                "reason": "vwap_reversal_long_rsi"
            }

        # 🔻 SHORT
        elif (high - vwap) / vwap >= entry_threshold and rsi_val >= rsi_overbought:
            sl = high + sl_percent * high
            risk = sl - entry
            tp = entry - reward_to_risk_ratio * risk

            if abs(tp - entry) / entry > max_tp_ratio:
                log.log(f"⚠️ TP too far for SELL: {tp:.2f} (>{max_tp_ratio * 100:.1f}%)", stock=stock)
                return {"signal": None, "reason": "tp_too_far_short"}

            log.log(f"✅ SELL signal | Entry: {entry:.2f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi_val:.2f}", stock=stock,
                    level="info")
            return {
                "signal": "SELL",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "market",
                "indicator": "VWAP+RSI",
                "reason": "vwap_reversal_short_rsi"
            }

        log.log("No VWAP+RSI signal detected", stock=stock, level="debug")
        return {"signal": None, "reason": "no_vwap_rsi_match"}

    except Exception as e:
        log.log(f"❌ Error calculating VWAP+RSI signal: {e}", stock=stock, level="error")
        return {"signal": None, "reason": f"error: {e}"}

def get_vwap(df):
    """
    Calcola il VWAP basato solo sui dati della giornata corrente (già filtrata) e aggiunge la colonna 'VWAP'
    al DataFrame di ingresso.
    """

    if df.empty or 'close' not in df.columns or 'volume' not in df.columns:
        return None

    # Assicura l'indice datetime (se necessario)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Calcolo VWAP solo per oggi (già filtrato per sessione corrente)
    df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

    return df