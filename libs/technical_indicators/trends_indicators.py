class TrendIndicators:
    def __init__(self, df):
        self.df = df.copy()

    def sma(self, period=20):
        self.df[f"SMA_{period}"] = self.df['Close'].rolling(window=period).mean()
        return self  # 🔁 NECESSARIO

    def ema(self, period=20):
        self.df[f"EMA_{period}"] = self.df['Close'].ewm(span=period, adjust=False).mean()
        return self  # 🔁 NECESSARIO

    def macd(self, fast=12, slow=26, signal=9):
        ema_fast = self.df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.df['Close'].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        self.df['MACD'] = macd
        self.df['MACD_signal'] = signal_line
        return self  # 🔁

    @property
    def result(self):
        return self.df