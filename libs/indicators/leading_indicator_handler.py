import pandas as pd

class LeadingIndicators:
    def __init__(self, df):
        """
        Initialize the LeadingIndicators class with a DataFrame.
        :param df: DataFrame containing 'Close', 'High', and 'Low' columns.
        """
        self.df = df

    def add_stochastic_oscillator(self, k_period=14, d_period=3):
        """
        Add Stochastic Oscillator to the DataFrame.
        It compares a closing price to its price range over a given time period.
        :param k_period: Number of periods for calculating %K.
        :param d_period: Number of periods for calculating %D (moving average of %K).
        :return: DataFrame with Stochastic Oscillator columns added.
        """
        self.df['Lowest_Low'] = self.df['Low'].rolling(window=k_period).min()
        self.df['Highest_High'] = self.df['High'].rolling(window=k_period).max()
        self.df['%K'] = (self.df['Close'] - self.df['Lowest_Low']) * 100 / (self.df['Highest_High'] - self.df['Lowest_Low'])
        self.df['%D'] = self.df['%K'].rolling(window=d_period).mean()
        return self.df

    def add_cci(self, period=20):
        """
        Add Commodity Channel Index (CCI) to the DataFrame.
        CCI identifies cyclical turns in commodities but can be used for other asset types.
        :param period: Number of periods for calculating CCI.
        :return: DataFrame with the CCI column added.
        """
        tp = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        cci = (tp - tp.rolling(window=period).mean()) / (0.015 * tp.rolling(window=period).std())
        self.df['CCI'] = cci
        return self.df
    
    def add_williams_r(self, period=14):
        """
        Add Williams %R to the DataFrame.
        Williams %R is a momentum indicator that measures overbought and oversold levels.
        :param period: Number of periods for calculating Williams %R.
        :return: DataFrame with Williams %R column added.
        """
        highest_high = self.df['High'].rolling(window=period).max()
        lowest_low = self.df['Low'].rolling(window=period).min()
        self.df['Williams_R'] = ((highest_high - self.df['Close']) / (highest_high - lowest_low)) * -100
        return self.df

    def add_parabolic_sar(self, af_step=0.02, af_max=0.2):
        """
        Add Parabolic SAR to the DataFrame.
        Parabolic SAR is used to determine the direction in which to trade and potential entry and exit points.
        :param af_step: Acceleration factor step value.
        :param af_max: Maximum acceleration factor.
        :return: DataFrame with Parabolic SAR column added.
        """
        sar = self.df['High'].iloc[0]
        ep = self.df['Low'].iloc[0]
        af = af_step
        sar_array = np.zeros(len(self.df))
        trend = 1  # 1 for uptrend, -1 for downtrend

        for i in range(1, len(self.df)):
            if trend == 1:  # uptrend
                sar = sar + af * (ep - sar)
                sar = min(sar, self.df['Low'].iloc[i - 1], self.df['Low'].iloc[i])
                if self.df['Close'].iloc[i] < sar:
                    trend = -1
                    sar = self.df['High'].iloc[i]
                    ep = self.df['High'].iloc[i]
                    af = af_step
            else:  # downtrend
                sar = sar - af * (sar - ep)
                sar = max(sar, self.df['High'].iloc[i - 1], self.df['High'].iloc[i])
                if self.df['Close'].iloc[i] > sar:
                    trend = 1
                    sar = self.df['Low'].iloc[i]
                    ep = self.df['Low'].iloc[i]
                    af = af_step

            sar_array[i] = sar
            if (trend == 1 and self.df['High'].iloc[i] > ep) or (trend == -1 and self.df['Low'].iloc[i] < ep):
                af = min(af + af_step, af_max)
                ep = self.df['High'].iloc[i] if trend == 1 else self.df['Low'].iloc[i]

        self.df['Parabolic_SAR'] = sar_array
        return self.df

    def add_momentum_indicator(self, period=10):
        """
        Add Momentum Indicator to the DataFrame.
        Momentum Indicator measures the rate of change in prices.
        :param period: Number of periods for calculating momentum.
        :return: DataFrame with Momentum Indicator column added.
        """
        self.df['Momentum'] = self.df['Close'].diff(period)
        return self.df

    def add_dpo(self, period=20):
        """
        Add Detrended Price Oscillator (DPO) to the DataFrame.
        DPO eliminates trends in prices to identify cycles and overbought/oversold levels.
        :param period: Number of periods for calculating DPO.
        :return: DataFrame with DPO column added.
        """
        displaced_sma = self.df['Close'].rolling(window=period).mean().shift(period // 2 + 1)
        self.df['DPO'] = self.df['Close'] - displaced_sma
        return self.df

    def add_all_indicators(self):
        """
        Add all leading indicators to the DataFrame.
        :return: DataFrame with all leading indicators added.
        """
        self.add_stochastic_oscillator()
        self.add_cci()
        self.add_williams_r()
        self.add_parabolic_sar()
        self.add_momentum_indicator()
        self.add_dpo()
        return self.df