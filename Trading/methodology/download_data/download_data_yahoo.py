import os
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

class StockDataDownloader:
    def __init__(self, stock_list, interval='1d'):
        self.tickers = stock_list
        self.interval = interval

        if interval == '1d':
            self.data_path = 'Trading/Data/Daily/'
        elif interval == '1wk':
            self.data_path = 'Trading/Data/Weekly/'
        else:
            raise ValueError("Invalid interval. Choose '1d' for daily or '1wk' for weekly data.")

        # Creare la cartella se non esiste
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

    def _download_data(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=20*365)  # 20 anni fa

        for ticker in self.tickers[:]:
            try:
                data = yf.download(ticker, start=start_date, end=end_date, interval=self.interval)
                data.to_csv(f"{self.data_path}/{ticker}_historical_data.csv")
            except Exception as e:
                print(f"Failed to download data for {ticker}: {e}")
                self.tickers.remove(ticker)  # Rimuovi il ticker dalla lista

    def update_data(self):
        end_date = datetime.now()

        # Assicurarsi che la cartella esista
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        
        for ticker in self.tickers[:]:
            csv_file = f"{self.data_path}/{ticker}_historical_data.csv"
            
            try:
                df = pd.read_csv(csv_file)
                if df.empty:
                    raise Exception("CSV file is empty")
                
                last_record = df.iloc[-1]
                last_date = pd.to_datetime(last_record['Date'])
                start_date = last_date + pd.Timedelta(days=1 if self.interval == '1d' else 7)

                if start_date < end_date:
                    new_data = yf.download(ticker, start=start_date, end=end_date, interval=self.interval)
                    new_data.to_csv(csv_file, mode='a', header=False)
                    print(f"Dati aggiornati per {ticker}")
                else:
                    print(f"{ticker} è già aggiornato.")

            except FileNotFoundError:
                print(f"Il file {csv_file} non esiste. Scarico tutto il dataset.")
                self._download_data()
            except (IndexError, Exception) as e:
                print(f"Errore durante la lettura o il download di {ticker}: {e}")
                self.tickers.remove(ticker)  # Rimuovi il ticker dalla lista