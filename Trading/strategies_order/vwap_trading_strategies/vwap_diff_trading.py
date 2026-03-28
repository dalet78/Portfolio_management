import pandas as pd
from datetime import datetime

SL_PERCENT = 0.007
TP_PERCENT = 0.014

def check_vwap_diff_signal(df, stock, log, trade_tracker,
                          entry_threshold=0.014,
                          sl_percent=0.007,
                          reward_to_risk_ratio=2.0,
                          max_tp_ratio=0.05):
    """Check for VWAP reversal signals and return a structured BUY/SELL signal."""

    log.log(f"Analyzing VWAP reversal signal for {stock}", stock=stock)

    try:
        # Crea 'date_only' se non esiste (per sicurezza)
        if 'date_only' not in df.columns:
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df.set_index('date', inplace=True)
                else:
                    raise ValueError("❌ 'date' column is missing and index is not a DatetimeIndex.")
            df['date_only'] = df.index.date

        # Filtra per la data odierna
        today = datetime.now().date()
        df_today = df[df['date_only'] == today].copy()

        # Rimuovi 'date_only' dopo il filtraggio
        df_today.drop(columns=['date_only'], inplace=True)

        df_vwap = get_vwap(df_today)
        if df_vwap is None or df_vwap.empty:
            return {"signal": None, "reason": "no_current_day_data"}

        last = df_vwap.iloc[-1]
        entry = last['close']
        high = last['high']
        low = last['low']
        vwap = last['VWAP']

        log.log(f"Close: {entry} | Low: {low} | High: {high} | VWAP: {vwap}", stock=stock)

        # Log delle differenze per l'ultima candela
        diff_low_pct = (vwap - low) / vwap * 100 if vwap != 0 else 0
        diff_high_pct = (high - vwap) / vwap * 100 if vwap != 0 else 0
        log.log(f"[{stock}] Last Candela: VWAP-Low={diff_low_pct:.2f}%, High-VWAP={diff_high_pct:.2f}%", stock=stock,
                level="debug")

        # 🟢 LONG
        if (vwap - low) / vwap >= entry_threshold:
            sl = low - sl_percent * low
            risk = entry - sl
            tp = entry + reward_to_risk_ratio * risk

            if tp < vwap:
                log.log(f"🔁 TP adjusted to VWAP for BUY: from {tp:.2f} to {vwap:.2f}", stock=stock, level="info")
                tp = vwap

            if abs(tp - entry) / entry > max_tp_ratio:
                log.log(f"⚠️ TP too far for BUY: {tp:.2f} (>{max_tp_ratio * 100:.1f}%)", stock=stock)
                return {"signal": None, "reason": "tp_too_far_long"}

            log.log(f"✅ BUY signal | Entry: {entry:.2f}, SL: {sl:.2f}, TP: {tp:.2f}", stock=stock, level="info")
            return {
                "signal": "BUY",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "market",
                "indicator": "VWAP",
                "reason": "vwap_reversal_long"
            }

        # 🔻 SHORT
        elif (high - vwap) / vwap >= entry_threshold:
            sl = high + sl_percent * high
            risk = sl - entry
            tp = entry - reward_to_risk_ratio * risk

            if tp > vwap:
                log.log(f"🔁 TP adjusted to VWAP for SELL: from {tp:.2f} to {vwap:.2f}", stock=stock, level="info")
                tp = vwap

            if abs(tp - entry) / entry > max_tp_ratio:
                log.log(f"⚠️ TP too far for SELL: {tp:.2f} (>{max_tp_ratio * 100:.1f}%)", stock=stock)
                return {"signal": None, "reason": "tp_too_far_short"}

            log.log(f"✅ SELL signal | Entry: {entry:.2f}, SL: {sl:.2f}, TP: {tp:.2f}", stock=stock, level="info")
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