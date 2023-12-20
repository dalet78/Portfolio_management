import pandas as pd
import pandas_ta as ta

class TrendAnalyzer:
    def __init__(self, df, period=14):
        self.df = df
        self.period = period

    def calculate_dmi(self):
        # Calcola differenze
        delta_high = self.df['High'].diff(1)
        delta_low = self.df['Low'].diff(1)

        # Identifica +DM e -DM
        dm_plus = (delta_high > delta_low) & (delta_high > 0)
        dm_minus = (delta_low > delta_high) & (delta_low > 0)

        # Assegna valori a +DM e -DM
        self.df['+DM'] = delta_high * dm_plus
        self.df['-DM'] = delta_low * dm_minus
        self.df['+DM'].fillna(0, inplace=True)
        self.df['-DM'].fillna(0, inplace=True)

        # Calcola True Range
        tr1 = self.df['High'] - self.df['Low']
        tr2 = abs(self.df['High'] - self.df['Close'].shift(1))
        tr3 = abs(self.df['Low'] - self.df['Close'].shift(1))
        self.df['TR'] = tr1.combine(tr2, max).combine(tr3, max)

        # Calcola medie mobili esponenziali
        self.df['+DI'] = 100 * self.df['+DM'].ewm(alpha=1 / self.period).mean() / self.df['TR']
        self.df['-DI'] = 100 * self.df['-DM'].ewm(alpha=1 / self.period).mean() / self.df['TR']
        self.df['DX'] = 100 * abs(self.df['+DI'] - self.df['-DI']) / (self.df['+DI'] + self.df['-DI'])
        self.df['ADX'] = self.df['DX'].ewm(alpha=1 / self.period).mean()

    def identify_trend(self):
        trend_type = []

        for _, row in self.df.iterrows():
            if row['ADX'] < 25:  # Consider ADX < 25 as a weak trend
                trend_type.append(0)
            elif row['+DI'] > row['-DI']:
                trend_type.append(2)
            elif row['-DI'] > row['+DI']:
                trend_type.append(1)
            else:
                trend_type.append(0)

        self.df['Trend'] = trend_type

    def add_trend_to_df(self):
        self.calculate_dmi()
        self.identify_trend()
        return self.df


