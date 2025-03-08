import pandas as pd
from pandas.api.types import is_any_real_numeric_dtype

class DataRefactory:
    """Classe per la preparazione e la pulizia dei DataFrame."""

    @staticmethod
    def prepare_5m_csv(filepath):
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
        # df = df.drop(index=[0, 1])
        df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce', utc=True)
        df.set_index('Datetime', inplace=True)
        df= df.sort_index()
        # df = df.apply(pd.to_numeric, errors='coerce')
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

