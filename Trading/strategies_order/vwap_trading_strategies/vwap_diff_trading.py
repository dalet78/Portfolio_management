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
        df = filter_today_data(df)  # ✅ applica il filtro

        df_today = get_today_vwap(df)
        if df_today is None or df_today.empty:
            return {"signal": None, "reason": "no_current_day_data"}

        last = df_today.iloc[-1]
        entry = last['close']
        high = last['high']
        low = last['low']
        vwap = last['VWAP']

        log.log(f"Close: {entry} | Low: {low} | High: {high} | VWAP: {vwap}", stock=stock)

        # 🟢 LONG
        if (vwap - low) / vwap >= entry_threshold:
            sl = low - sl_percent * low
            risk = entry - sl
            tp = entry + reward_to_risk_ratio * risk

            # Filtro TP troppo distante
            if abs(tp - entry) / entry > max_tp_ratio:
                log.log(f"⚠️ TP too far for BUY: {tp:.2f} (>{max_tp_ratio*100:.1f}%)", stock=stock)
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

            # Filtro TP troppo distante
            if abs(tp - entry) / entry > max_tp_ratio:
                log.log(f"⚠️ TP too far for SELL: {tp:.2f} (>{max_tp_ratio*100:.1f}%)", stock=stock)
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

def filter_today_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra il DataFrame mantenendo solo le righe relative alla data odierna.

    Args:
        df (pd.DataFrame): DataFrame con indice datetime.

    Returns:
        pd.DataFrame: Solo i dati della giornata corrente.
    """
    if df.empty:
        return df

    df = df.copy()
    df.index = pd.to_datetime(df.index)
    today = datetime.now().date()
    return df[df.index.date == today]

def get_today_vwap(df):
    """
    Filtra il DataFrame per la data corrente (ultima data presente) e calcola il VWAP
    basato solo sui dati della giornata.

    Args:
        df (pd.DataFrame): DataFrame con almeno le colonne ['close', 'volume'].
                           L'indice deve essere DatetimeIndex.

    Returns:
        pd.DataFrame: DataFrame filtrato con i dati della giornata corrente e colonna 'VWAP'.
                      Restituisce None se dati insufficienti.
    """

    if df.empty or 'close' not in df.columns or 'volume' not in df.columns:
        return None

    # Assicura l'indice datetime
    df = df.copy()
    df.index = pd.to_datetime(df.index)

    # Estrai la data corrente (ultima nel DataFrame)
    current_date = df.index[-1].date()

    # Filtra solo le righe della giornata corrente
    df_today = df[df.index.date == current_date].copy()

    if df_today.empty:
        return None

    # Calcolo VWAP solo per oggi
    df_today['VWAP'] = (df_today['close'] * df_today['volume']).cumsum() / df_today['volume'].cumsum()

    return df_today