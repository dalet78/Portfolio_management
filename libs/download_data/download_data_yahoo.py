import os
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import shutil

source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
class StockDataDownloader:
    def __init__(self, stock_list, interval='1d', index = "SP500"):
        self.tickers = stock_list
        self.interval = interval

        if interval == '1d' and index == "SP500":
            self.data_path = f'{source_directory}/Data/SP500/Daily/'
        elif interval == '1wk'and index == "SP500":
            self.data_path = f'{source_directory}/Data/SP500/Weekly/'
        elif interval == '1d' and index == "Russel":
            self.data_path = f'{source_directory}/Data/Russel/Daily/'
        elif interval == '1wk'and index == "Russel":
            self.data_path = f'{source_directory}/Data/Russel/Weekly/'
        elif interval == '1d' and index == "Nasdaq":
            self.data_path = f'{source_directory}/Data/Nasdaq/Daily/'
        elif interval == '1wk'and index == "Nasdaq":
            self.data_path = f'{source_directory}/Data/Nasdaq/Weekly/'
        else:
            raise ValueError("Invalid interval. Choose '1d' for daily or '1wk' for weekly data.")

        # Creare la cartella se non esiste
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

    def download_data(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2*365)  # 20 anni fa
        self.delete_folder_contents(self.data_path)
        for ticker in self.tickers[:]:
            try:
                data = yf.download(ticker, start=start_date, end=end_date, interval=self.interval)
                data.to_csv(f"{self.data_path}{ticker}_historical_data.csv")
                print(f"Dati aggiornati per {ticker}")
            except Exception as e:
                print(f"Failed to download data for {ticker}: {e}")
                self.tickers.remove(ticker)  # Rimuovi il ticker dalla lista


    def update_data(self):
        end_date = datetime.now()

        # Assicurarsi che la cartella esista
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        
        for ticker in self.tickers[:]:
            csv_file = f"{self.data_path}{ticker}_historical_data.csv"
            
            try:
                df = pd.read_csv(csv_file, index_col='Date')
                df.index = pd.to_datetime(df.index)

                if df.empty:
                    raise Exception("CSV file is empty")

                last_date = df.index[-1]
                start_date = last_date + pd.Timedelta(days=1 if self.interval == '1d' else 7)

                if start_date < end_date:
                    new_data = yf.download(ticker, start=start_date, end=end_date, interval=self.interval)
                    new_data.index = pd.to_datetime(new_data.index)

                    # Rimuovere i duplicati
                    combined_df = pd.concat([df, new_data]).drop_duplicates()

                    # Salvare i dati aggiornati
                    combined_df.to_csv(csv_file)
                    print(f"Dati aggiornati per {ticker}")
                else:
                    print(f"{ticker} è già aggiornato.")

            except FileNotFoundError:
                print(f"Il file {csv_file} non esiste. Scarico tutto il dataset.")
                self._download_data()
            except (IndexError, Exception) as e:
                print(f"Errore durante la lettura o il download di {ticker}: {e}")
                self.tickers.remove(ticker)  # Rimuovi il ticker dalla lista

    def delete_folder_contents(self, folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')