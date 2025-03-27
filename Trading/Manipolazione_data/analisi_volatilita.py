import os
import numpy as np
import pandas as pd
from support.data_preparation import DataRefactory

def correlazione_classica(df1, df2):
    # Calcola i rendimenti percentuali
    returns1 = df1['Close'].pct_change().dropna()
    returns2 = df2['Close'].pct_change().dropna()

    # Rimuove eventuali indici duplicati
    returns1 = returns1[~returns1.index.duplicated()]
    returns2 = returns2[~returns2.index.duplicated()]

    # Allinea le due serie per indice comune
    combined = pd.concat([returns1, returns2], axis=1, join='inner').dropna()
    combined.columns = ['SPY', 'TGT']

    return combined.corr().iloc[0, 1]  # Pearson correlation SPY vs TGT

def lagged_correlation(x, y, max_lag=10):
    result = {}
    for lag in range(1, max_lag + 1):
        if len(x) > lag and len(y) > lag:
            result[lag] = np.corrcoef(x[:-lag], y[lag:])[0, 1]
    return result

def rolling_beta(x, y, window=30):
    betas = []
    for i in range(len(x) - window):
        x_win = x[i:i+window]
        y_win = y[i:i+window]
        var_x = np.var(x_win)
        if var_x != 0:
            beta = np.cov(x_win, y_win)[0][1] / var_x
            betas.append(beta)
    return np.mean(betas) if betas else np.nan

def volatility(df):
    return df['Close'].pct_change().std()

# === CONFIG ===
stock1 = "SPY"
stock2 = "QQQ"
DATA_DIRECTORY = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
ALL_DATA_PATH = f"{DATA_DIRECTORY}/Data/INDEX/5min"
REPORT_PATH = "Reports/Data/tmp"

# === FILES ===
report_folder = os.path.join(DATA_DIRECTORY, REPORT_PATH, f"{stock1}_{stock2}")
os.makedirs(report_folder, exist_ok=True)

file1 = os.path.join(ALL_DATA_PATH, f"{stock1}_historical_data.csv")
file2 = os.path.join(ALL_DATA_PATH, f"{stock2}_historical_data.csv")

df1 = DataRefactory.prepare_5m_csv(filepath=file1)
df2 = DataRefactory.prepare_5m_csv(filepath=file2)

# === CALCOLI ===
returns1 = df1['Close'].pct_change().dropna()
returns2 = df2['Close'].pct_change().dropna()

# Rimuovi duplicati dall'indice (tipicamente datetime)
returns1 = returns1[~returns1.index.duplicated()]
returns2 = returns2[~returns2.index.duplicated()]

# Allinea sullo stesso indice
aligned = pd.concat([returns1, returns2], axis=1, join='inner').dropna()
aligned.columns = ['ref', 'target']


pearson_corr = correlazione_classica(df1, df2)
lag_corrs = lagged_correlation(aligned['ref'].values, aligned['target'].values)
beta = rolling_beta(aligned['ref'].values, aligned['target'].values)
vol1 = volatility(df1)
vol2 = volatility(df2)

# === SAVE RESULTS ===
result = {
    "Reference": stock1,
    "Target": stock2,
    "Pearson Correlation": pearson_corr,
    "Max Lagged Correlation": max(lag_corrs.values()),
    "Lag of Max Correlation": max(lag_corrs, key=lag_corrs.get),
    f"Volatility {stock1}": vol1,
    f"Volatility {stock2}": vol2,
    "Rolling Beta": beta
}

result_path = os.path.join(report_folder, f"correlation_analysis_{stock1}_{stock2}.csv")
pd.DataFrame([result]).to_csv(result_path, index=False)

result_path, result

