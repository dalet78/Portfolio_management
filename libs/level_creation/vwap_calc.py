import pandas as pd


class VWAPCalculator:
    def __init__(self, df: pd.DataFrame):
        """
        Classe per calcolare il VWAP su diversi timeframe.
        :param df: DataFrame con colonne ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
        """
        self.df = df.copy()
        self.df['Datetime'] = pd.to_datetime(self.df['Datetime'])
        self.df = self.df.sort_values('Datetime')

    def calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcola il VWAP su un sottoinsieme del DataFrame e aggiunge la variazione percentuale.
        """
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        df['VWAP_Change'] = df['VWAP'].pct_change() * 100
        df['VWAP_Std'] = df['Close'].rolling(window=20).std()  # Deviazione standard su 20 periodi
        df['VWAP_Upper'] = df['VWAP'] + df['VWAP_Std']
        df['VWAP_Lower'] = df['VWAP'] - df['VWAP_Std']
        return df

    def calculate_vwap_daily(self) -> pd.DataFrame:
        """
        Calcola il VWAP giornaliero a date fisse.
        """
        self.df['Date'] = self.df['Datetime'].dt.floor('D')
        return self.df.groupby('Date').apply(self.calculate_vwap)

    def calculate_vwap_weekly(self) -> pd.DataFrame:
        """
        Calcola il VWAP settimanale con riferimento alla settimana ISO.
        """
        self.df['Week'] = self.df['Datetime'].dt.isocalendar().week
        return self.df.groupby('Week').apply(self.calculate_vwap)

    def calculate_vwap_monthly(self) -> pd.DataFrame:
        """
        Calcola il VWAP mensile con riferimento al mese calendario.
        """
        self.df['Month'] = self.df['Datetime'].dt.to_period('M').astype(str)
        return self.df.groupby('Month').apply(self.calculate_vwap)

    def calculate_vwap_quadrimestrale(self) -> pd.DataFrame:
        """
        Calcola il VWAP quadrimestrale basato su periodi fissi (Gen-Apr, Mag-Ago, Set-Dic).
        """
        self.df['Quadrimestre'] = self.df['Datetime'].dt.month.map(lambda x: (x - 1) // 4 + 1)
        self.df['Anno_Quadrimestre'] = self.df['Datetime'].dt.year.astype(str) + '-Q' + self.df['Quadrimestre'].astype(
            str)
        return self.df.groupby('Anno_Quadrimestre').apply(self.calculate_vwap)
