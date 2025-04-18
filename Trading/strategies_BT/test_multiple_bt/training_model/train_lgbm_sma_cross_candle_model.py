# Versione aggiornata dello script con nuove feature: volume_ratio, gap, day_of_week
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from lightgbm import LGBMClassifier
from joblib import dump

from libs.filtered_stock import return_filtred_list
from support.data_preparation import DataRefactory
from libs.technical_indicators.trends_indicators import TrendIndicators
from libs.technical_indicators.volume_indicators import VolumeIndicators
from libs.technical_indicators.momentum_indicators import MomentumIndicators
from libs.technical_indicators.volatility_indicators import VolatilityIndicators

# CONFIG
DATA_DIR = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Data/ALL/5min"
OUTPUT_MODEL_PATH_BUY = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Models/model_sma3candle_buy.joblib"
OUTPUT_MODEL_PATH_SELL = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Models/model_sma3candle_sell.joblib"
TP_THRESHOLD = 0.014
SL_THRESHOLD = -0.007
FUTURE_CANDLES = 20

def calculate_features(df):
    df = VolumeIndicators(df).vwap().result
    df = TrendIndicators(df).sma(5).sma(20).result
    df = MomentumIndicators(df).rsi(14).result
    df = VolatilityIndicators(df).atr(14).result
    df['volume_ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
    df['prev_close'] = df['Close'].shift(1)
    df['gap'] = df['Open'] - df['prev_close']
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df['day_of_week'] = df.index.dayofweek
    return df.dropna()

def extract_signals(df):
    buy_signals, sell_signals = [], []
    df['date'] = df.index.date
    for _, group in df.groupby('date'):
        if len(group) < 10:
            continue
        sub, future = group.iloc[:3], group.iloc[3:3+FUTURE_CANDLES]
        if len(future) < FUTURE_CANDLES: continue

        sma5_now, sma20_now = sub['SMA_5'].iloc[-1], sub['SMA_20'].iloc[-1]
        sma5_prev, sma20_prev = sub['SMA_5'].iloc[-2], sub['SMA_20'].iloc[-2]
        candle = sub.iloc[-1]
        entry = candle['Close']
        max_fut, min_fut = future['High'].max(), future['Low'].min()

        # BUY
        if sma5_prev <= sma20_prev and sma5_now > sma20_now:
            if (max_fut - entry) / entry >= TP_THRESHOLD:
                target = 1  # Take Profit raggiunto
            elif (min_fut - entry) / entry <= SL_THRESHOLD:
                target = 0  # Stop Loss colpito
            else:
                continue  # caso ambiguo, lo saltiamo

            buy_signals.append({
                'timestamp': candle.name,
                'SMA_5': candle['SMA_5'],
                'SMA_20': candle['SMA_20'],
                'sma_ratio': candle['SMA_5'] / candle['SMA_20'],
                'volume_ratio': candle['volume_ratio'],
                # 'VWAP': candle['VWAP'],
                'gap': candle['gap'],
                # 'RSI_14': candle['RSI_14'],
                'ATR_14': candle['ATR_14'],
                'target': target
            })

        # SELL
        elif sma5_prev >= sma20_prev and sma5_now < sma20_now:
            if (entry - min_fut) / entry >= TP_THRESHOLD:
                target = 1  # Take Profit raggiunto (in discesa)
            elif (entry - max_fut) / entry <= SL_THRESHOLD:
                target = 0  # Stop Loss colpito
            else:
                continue  # caso ambiguo, lo saltiamo

            sell_signals.append({
                'timestamp': candle.name,
                'SMA_5': candle['SMA_5'],
                'SMA_20': candle['SMA_20'],
                'sma_ratio': candle['SMA_5'] / candle['SMA_20'],
                'volume_ratio': candle['volume_ratio'],
                # 'VWAP': candle['VWAP'],
                'gap': candle['gap'],
                # 'RSI_14': candle['RSI_14'],
                'ATR_14': candle['ATR_14'],
                'target': target
            })

    return pd.DataFrame(buy_signals), pd.DataFrame(sell_signals)

def load_all_signals():
    all_buy, all_sell = [], []
    for stock in return_filtred_list("ALL", price_range= (10,200)):
        try:
            df = DataRefactory.prepare_min_csv(f"{DATA_DIR}/{stock}_historical_data.csv")
            df = calculate_features(df)
            df_buy, df_sell = extract_signals(df)
            all_buy.append(df_buy)
            all_sell.append(df_sell)
        except Exception as e:
            print(f"❌ Errore su {stock}: {e}")
    return pd.concat(all_buy).dropna(), pd.concat(all_sell).dropna()

def plot_importance(model, X, title):
    fi = pd.Series(model.feature_importances_, index=X.columns).sort_values()
    plt.figure(figsize=(8, 5))
    sns.barplot(x=fi.values, y=fi.index)
    plt.title(title)
    plt.tight_layout()
    plt.show()


# === Train & Save ===
df_buy, df_sell = load_all_signals()

Xb, yb = df_buy.drop(columns=['timestamp', 'target']), df_buy['target'].astype(int)
Xs, ys = df_sell.drop(columns=['timestamp', 'target']), df_sell['target'].astype(int)

Xb_train, Xb_test, yb_train, yb_test = train_test_split(Xb, yb, test_size=0.2, shuffle=False)
Xs_train, Xs_test, ys_train, ys_test = train_test_split(Xs, ys, test_size=0.2, shuffle=False)

model_buy = LGBMClassifier(class_weight='balanced')
model_buy.fit(Xb_train, yb_train)
print("📈 BUY MODEL\n", classification_report(yb_test, model_buy.predict(Xb_test)))
dump(model_buy, OUTPUT_MODEL_PATH_BUY)

model_sell = LGBMClassifier()
model_sell.fit(Xs_train, ys_train)
print("📉 SELL MODEL\n", classification_report(ys_test, model_sell.predict(Xs_test)))
dump(model_sell, OUTPUT_MODEL_PATH_SELL)

print("✅ Modelli salvati:")
print(f" - BUY  → {OUTPUT_MODEL_PATH_BUY}")
print(f" - SELL → {OUTPUT_MODEL_PATH_SELL}")

plot_importance(model_buy, Xb, "BUY Feature Importance")
plot_importance(model_sell, Xs, "SELL Feature Importance")
