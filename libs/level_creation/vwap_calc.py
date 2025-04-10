import pandas as pd


class VWAPCalculator:
    def __init__(self, df: pd.DataFrame):
        """
        Classe per calcolare il VWAP su diversi timeframe.
        :param df: DataFrame con colonne ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
        """
        self.df = df.copy()
        if self.df.index.name != 'Datetime':
            self.df.index = pd.to_datetime(self.df.index)
            self.df.index.name = 'Datetime'
        self.df = self.df.sort_index()

    def calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcola il VWAP su un sottoinsieme del DataFrame e aggiunge la variazione percentuale.
        """
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        cum_vol = df['Volume'].cumsum()
        cum_pv = (typical_price * df['Volume']).cumsum()
        df['VWAP'] = cum_pv / cum_vol
        df['VWAP_Change'] = df['VWAP'].pct_change() * 100
        df['VWAP_Std'] = df['Close'].rolling(window=20).std()  # Deviazione standard su 20 periodi
        df['VWAP_Upper'] = df['VWAP'] + df['VWAP_Std']
        df['VWAP_Lower'] = df['VWAP'] - df['VWAP_Std']
        return df

    def calculate_vwap_daily(self) -> pd.DataFrame:
        self.df['Date'] = self.df.index.date
        grouped = []
        for date, group in self.df.groupby('Date'):
            group = self.calculate_vwap(group)
            grouped.append(group)
        return pd.concat(grouped).sort_values('Datetime')

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
