import pandas as pd
from pandas.api.types import is_any_real_numeric_dtype

class DataRefactory:
    """Classe per la preparazione e la pulizia dei DataFrame."""

    @staticmethod
    def prepare_min_csv(filepath):
        """Carica e prepara i dati da un file CSV con timeframe 5m."""
        df = pd.read_csv(filepath)
        df = df.rename(columns={
            'date': 'Datetime',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce', utc=True)
        df.set_index('Datetime', inplace=True)
        df = df.sort_index()
        return df

    @staticmethod
    def calculate_pivot_points( df):
        """Calcola i Pivot Points basati sul giorno precedente."""

        # Identificare i giorni separati
        df['Date'] = df.index.date  # Estrae solo la data senza orario

        # Calcolo dei livelli del giorno precedente
        prev_day_data = df.groupby('Date').agg({
            'Close': 'last',
            'High': 'max',
            'Low': 'min'
        }).shift(1)  # Spostiamo di un giorno indietro

        prev_day_data.rename(columns={'Close': 'PDC', 'High': 'PDH', 'Low': 'PDL'}, inplace=True)

        # Merge dei valori nel dataset originale
        df = df.merge(prev_day_data, left_on='Date', right_index=True, how='left')

        # Calcolo dei Pivot Points
        df['PP'] = (df['PDH'] + df['PDL'] + df['PDC']) / 3
        df['R1'] = (2 * df['PP']) - df['PDL']
        df['S1'] = (2 * df['PP']) - df['PDH']

        # Eliminare la colonna temporanea 'Date'
        df.drop(columns=['Date'], inplace=True)

        return df

    @staticmethod
    def prepare_daily_csv(filepath):
        """Carica e prepara i dati da un file CSV con timeframe daily."""
        df = pd.read_csv(filepath)
        df = df.rename(columns={'Price': 'Date'})
        df = df.drop(index=[0, 1])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.set_index('Date', inplace=True)
        df = df.apply(pd.to_numeric, errors='coerce')
        return df

    @staticmethod
    def convert_5m_to_10m(df):
        """Converte un DataFrame da timeframe 5 minuti a 10 minuti aggregando i dati."""
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Il parametro df deve essere un DataFrame di Pandas")

        # Correzione della sintassi per il resample
        df_10min = df.resample('10min').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })

        # Rimuove eventuali righe con NaN
        df_10min.dropna(inplace=True)

        # Calcolo dei livelli del giorno precedente (spostamento di 1 giorno)
        df_10min = DataRefactory.calculate_pivot_points(df_10min)

        # **Calcoliamo il VWAP**
        df_10min = DataRefactory.calculate_vwap(df_10min)

        return df_10min

    @staticmethod
    def convert_5m_to_15m(df):
        """Converte un DataFrame da timeframe 5 minuti a 15 minuti aggregando i dati."""
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Il parametro df deve essere un DataFrame di Pandas")

        # Aggrega i dati in intervalli di 15 minuti
        df_15min = df.resample('15min').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })

        # Rimuove eventuali righe con NaN
        df_15min.dropna(inplace=True)

        # **Calcolo dei livelli del giorno precedente (pivot points)**
        df_15min = DataRefactory.calculate_pivot_points(df_15min)

        # **Calcoliamo il VWAP**
        df_15min = DataRefactory.calculate_vwap(df_15min)

        return df_15min

    @staticmethod
    def calculate_vwap(df):
        """Calcola il VWAP (Volume Weighted Average Price)."""
        df['CumVolume'] = df['Volume'].cumsum()
        df['CumPriceVolume'] = (df['Close'] * df['Volume']).cumsum()
        df['VWAP'] = df['CumPriceVolume'] / df['CumVolume']

        # Rimuove colonne intermedie
        df.drop(columns=['CumVolume', 'CumPriceVolume'], inplace=True)

        return df


