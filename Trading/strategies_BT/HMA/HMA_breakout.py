from datetime import time
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import numpy as np
import pandas as pd

# Orari strategia
STRATEGY_START_TIME = time(16, 30)  # Inizia 1 ora dopo l'apertura
STRATEGY_END_TIME = time(18, 30)  # Termina dopo 2 ore
FORCE_EXIT_TIME = time(20, 50)  # Chiude tutte le posizioni a fine giornata


def WMA(series, period):
    """Calcola la Weighted Moving Average (WMA)"""
    weights = np.arange(1, period + 1)
    return series.rolling(period).apply(lambda prices: np.dot(prices, weights) / weights.sum(), raw=True)


def HMA(series, period):
    """Calcola la Hull Moving Average (HMA) compatibile con Backtesting.py"""
    series = pd.Series(series)  # Converte in Pandas Series se necessario

    if len(series) < period:
        return np.full(len(series), np.nan)  # Se non ci sono abbastanza dati, restituisce NaN

    half_length = period // 2
    sqrt_length = int(np.sqrt(period))

    # Calcolo delle medie ponderate
    wma_half = WMA(series, half_length)
    wma_full = WMA(series, period)

    # Se una delle WMA è completamente NaN, restituiamo NaN
    if wma_half.isna().all() or wma_full.isna().all():
        return np.full(len(series), np.nan)

    hma = WMA(2 * wma_half - wma_full, sqrt_length)

    # Riempie NaN e converte in NumPy array
    return hma.fillna(method="bfill").fillna(method="ffill").to_numpy()

def get_previous_day_levels(df_daily):
    """
    Calcola i livelli di supporto e resistenza basati sul giorno precedente.

    :param df_daily: DataFrame con dati giornalieri (colonne: Date, Open, High, Low, Close)
    :return: Dizionario con livelli di supporto e resistenza
    """
    df_daily = df_daily.sort_index()
    if len(df_daily) < 2:
        return None  # Non ci sono abbastanza dati

    previous_day = df_daily.iloc[-2]  # Giorno precedente

    levels = {
        "resistenza_1": previous_day["High"],  # Massimo del giorno precedente
        "supporto_1": previous_day["Low"],  # Minimo del giorno precedente
        "chiusura_precedente": previous_day["Close"],  # Prezzo di chiusura del giorno prima
    }

    return levels


def get_previous_week_levels(df_daily):
    """
    Calcola i livelli di supporto e resistenza basati sulla settimana precedente.

    :param df_daily: DataFrame con dati giornalieri (colonne: Date, Open, High, Low, Close)
    :return: Dizionario con livelli di supporto e resistenza settimanali
    """
    df_daily = df_daily.sort_index()

    if len(df_daily) < 10:
        return None  # Non abbastanza dati

    last_trading_day = df_daily.index[-1]
    previous_week = df_daily.loc[df_daily.index < last_trading_day].iloc[-5:]

    levels = {
        "resistenza_settimanale": previous_week["High"].max(),
        "supporto_settimanale": previous_week["Low"].min(),
        "chiusura_settimanale": previous_week.iloc[-1]["Close"],
    }

    return levels

def ADX(high, low, close, period=14):
    """Calcola l'Average Directional Index (ADX) per filtrare i mercati laterali"""
    df = pd.DataFrame({'High': high, 'Low': low, 'Close': close})
    df['TR'] = df['High'].combine(df['Close'].shift(), max) - df['Low'].combine(df['Close'].shift(), min)
    df['DM+'] = df['High'].diff().apply(lambda x: x if x > 0 else 0)
    df['DM-'] = -df['Low'].diff().apply(lambda x: x if x < 0 else 0)

    df['TR'] = df['TR'].rolling(period).sum()
    df['DM+'] = df['DM+'].rolling(period).sum()
    df['DM-'] = df['DM-'].rolling(period).sum()

    df['DI+'] = 100 * df['DM+'] / df['TR']
    df['DI-'] = 100 * df['DM-'] / df['TR']
    df['DX'] = 100 * abs(df['DI+'] - df['DI-']) / (df['DI+'] + df['DI-'])

    adx = df['DX'].rolling(period).mean()
    return adx.fillna(20).to_numpy()

class HMABreakoutStrategy(Strategy):
    SL_PERCENT = 0.007  # 0.7%
    TP_PERCENT = 0.014  # 1.4%

    def init(self):
        """Inizializza gli indicatori HMA"""
        if len(self.data.Close) < 50:
            raise RuntimeError("Dati insufficienti per calcolare HMA")

        # Log per verificare i dati prima del calcolo
        print(f"Numero di dati disponibili: {len(self.data.Close)}")

        self.hma_fast = self.I(HMA, self.data.Close, 9)
        self.hma_slow = self.I(HMA, self.data.Close, 50)
        self.adx = self.I(ADX, self.data.High, self.data.Low, self.data.Close, 14)

        # Calcola i livelli giornalieri e settimanali una sola volta
        self.previous_day_levels = get_previous_day_levels(self.data.df)
        self.previous_week_levels = get_previous_week_levels(self.data.df)

    def next(self):
        """Logica di trading basata su HMA + supporto/resistenza + filtro ADX"""
        current_time = self.data.index[-1].time()

        # Controlla se siamo nel periodo della strategia
        if current_time < STRATEGY_START_TIME or current_time > STRATEGY_END_TIME:
            return

        # Filtro ADX: Evita operazioni in mercati laterali
        if self.adx[-1] < 20:
            return  # Non opera se ADX è inferiore a 20 (trend troppo debole)

        # Estrarre livelli di supporto e resistenza
        resistenza_1 = self.previous_day_levels["resistenza_1"]
        supporto_1 = self.previous_day_levels["supporto_1"]
        resistenza_settimanale = self.previous_week_levels["resistenza_settimanale"]
        supporto_settimanale = self.previous_week_levels["supporto_settimanale"]

        prezzo_attuale = self.data.Close[-1]

        # Segnale di ingresso LONG (solo se sopra un livello chiave)
        if (
            crossover(self.hma_fast, self.hma_slow)
            and (prezzo_attuale > resistenza_1 or prezzo_attuale > resistenza_settimanale)
        ):
            self.buy(
                sl=prezzo_attuale * (1 - self.SL_PERCENT),
                tp=prezzo_attuale * (1 + self.TP_PERCENT),
            )

        # Segnale di ingresso SHORT (solo se sotto un livello chiave)
        elif (
            crossover(self.hma_slow, self.hma_fast)
            and (prezzo_attuale < supporto_1 or prezzo_attuale < supporto_settimanale)
        ):
            self.sell(
                sl=prezzo_attuale * (1 + self.SL_PERCENT),
                tp=prezzo_attuale * (1 - self.TP_PERCENT),
            )

        # Forza la chiusura di tutte le posizioni a fine giornata
        if current_time >= FORCE_EXIT_TIME:
            self.position.close()