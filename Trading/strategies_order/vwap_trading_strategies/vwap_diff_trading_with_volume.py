import pandas as pd
from datetime import datetime, time


def check_vwap_diff_signal_with_volume(df, stock, log, trade_tracker,
                           entry_threshold=0.014,
                           sl_percent=0.007,
                           reward_to_risk_ratio=2.0,
                           max_tp_ratio=0.05,
                           volume_period=20,
                           volume_ratio_limit=2.0):
    """Check for VWAP reversal signals using Volume Ratio as filter."""

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

        df['volume_ma'] = df['volume'].rolling(window=volume_period).mean()

        # Filtra per la data odierna
        today = datetime.now().date()
        df_today = df[df['date_only'] == today].copy()

        # Rimuovi 'date_only' dopo il filtraggio
        df_today.drop(columns=['date_only'], inplace=True)

        if df_today.empty or len(df_today) < volume_period:
            return {"signal": None, "reason": "not_enough_data_today"}

        # Calcolo VWAP e media volume
        df_today = get_vwap(df_today)

        last = df_today.iloc[-1]
        entry = last['close']
        high = last['high']
        low = last['low']
        vwap = last['VWAP']
        volume = last['volume']
        volume_ma = last['volume_ma']

        if pd.isna(volume_ma) or volume_ma == 0:
            return {"signal": None, "reason": "invalid_volume_ma"}

        volume_ratio = volume / volume_ma
        log.log(f"Close: {entry} | Low: {low} | High: {high} | VWAP: {vwap} | Volume Ratio: {volume_ratio:.2f}", stock=stock)

        # Log delle differenze per l'ultima candela
        diff_low_pct = (vwap - low) / vwap * 100 if vwap != 0 else 0
        diff_high_pct = (high - vwap) / vwap * 100 if vwap != 0 else 0
        log.log(f"[{stock}] Last Candle: VWAP-Low={diff_low_pct:.2f}%, High-VWAP={diff_high_pct:.2f}%", stock=stock, level="debug")

        if volume_ratio >= volume_ratio_limit:
            return {"signal": None, "reason": "volume_too_high"}

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

            log.log(f"✅ BUY signal | Entry: {entry:.2f}, SL: {sl:.2f}, TP: {tp:.2f}, Volume Ratio: {volume_ratio:.2f}",
                    stock=stock, level="info")
            return {
                "signal": "BUY",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "market",
                "indicator": "VWAP+VolumeRatio",
                "reason": "vwap_reversal_long_volume"
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

            log.log(f"✅ SELL signal | Entry: {entry:.2f}, SL: {sl:.2f}, TP: {tp:.2f}, Volume Ratio: {volume_ratio:.2f}",
                    stock=stock, level="info")
            return {
                "signal": "SELL",
                "entry_price": entry,
                "sl": sl,
                "tp": tp,
                "order_type": "market",
                "indicator": "VWAP+VolumeRatio",
                "reason": "vwap_reversal_short_volume"
            }

        log.log("No VWAP+VolumeRatio signal detected", stock=stock, level="debug")
        return {"signal": None, "reason": "no_vwap_volume_match"}

    except Exception as e:
        log.log(f"❌ Error calculating VWAP+Volume signal: {e}", stock=stock, level="error")
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