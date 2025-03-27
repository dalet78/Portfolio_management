import os
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from support.data_preparation import DataRefactory


def aggiungi_colonne_pair_trading(df1, df2):
    df = pd.DataFrame({
        'x': df1['Close'].values,
        'y': df2['Close'].values
    })

    model = LinearRegression()
    model.fit(df[['x']], df['y'])
    df['y_pred'] = model.predict(df[['x']])

    df['spread'] = df['y'] - df['y_pred']
    df['zscore'] = (df['spread'] - df['spread'].rolling(window=30).mean()) / df['spread'].rolling(window=30).std()

    # ✅ Normalizzazione vera: differenza relativa simmetrica
    df['diff_norm'] = (df['x'] - df['y']) / ((df['x'] + df['y']) / 2)

    return df


def plot_distribuzioni(df, output_dir):
    colonne = ['spread', 'zscore', 'diff_norm']

    for col in colonne:
        counts = df[col].round(3).value_counts().sort_index()

        plt.figure(figsize=(10, 4))
        plt.bar(counts.index, counts.values, width=0.005)
        plt.title(f'Distribuzione di {col}')
        plt.xlabel(f'{col} (arrotondato a 3 decimali)')
        plt.ylabel('Frequenza')
        plt.grid(True)
        plt.tight_layout()

        # ✅ Salva il grafico
        plot_path = f"{output_dir}/{col}_distribuzione.png"
        plt.savefig(plot_path)
        print(f"📊 Grafico salvato: {plot_path}")
        plt.close()


# --- MAIN ---

stock1 = "SPY"
stock2 = "SPLG"
DATA_DIRECTORY = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
ALL_DATA_PATH = f"{DATA_DIRECTORY}/Data/INDEX/5min"
REPORT_PATH= "/Reports/Data/tmp"

# ✅ Crea cartella report specifica per la coppia
report_folder = f"{DATA_DIRECTORY}/{REPORT_PATH}/{stock1}_{stock2}"
os.makedirs(report_folder, exist_ok=True)

# Carica dati
file1 = f"{ALL_DATA_PATH}/{stock1}_historical_data.csv"
file2 = f"{ALL_DATA_PATH}/{stock2}_historical_data.csv"

df1 = DataRefactory.prepare_5m_csv(filepath=file1)
df2 = DataRefactory.prepare_5m_csv(filepath=file2)
df = aggiungi_colonne_pair_trading(df1, df2)

# Salva CSV
csv_path = f"{report_folder}/pair_trading_{stock1}_{stock2}.csv"
df.to_csv(csv_path, index=False)
print(f"✅ File CSV salvato in: {csv_path}")

# Salva i grafici
plot_distribuzioni(df, report_folder)
