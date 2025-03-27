import os
import yfinance as yf
from datetime import datetime, time, timedelta
import pandas as pd
import shutil
from support.data_preparation import DataRefactory

source_directory ="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
class StockDataDownloader:
    def __init__(self, stock_list, interval='1d', index = "SP500"):
        self.tickers = stock_list
        self.interval = interval

        if interval == '1d' and index == "ALL":
            self.data_path = f'{source_directory}/Data/ALL/Daily/'
        elif interval == '1wk' and index == "ALL":
            self.data_path = f'{source_directory}/Data/ALL/Weekly/'
        elif interval == '5m' and index == "ALL":
            self.data_path = f'{source_directory}/Data/ALL/5min/'
        else:
            raise ValueError("Invalid interval. Choose '1d' for daily or '1wk' for weekly data.")

        # Creare la cartella se non esiste
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

    def download_data(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2*365)
        self.delete_folder_contents(self.data_path)
        print(f"Inizio a scaricare dati per stocks {self.interval}")
        for ticker in self.tickers[:]:
            try:
                data = yf.download(ticker, start=start_date, end=end_date, interval=self.interval)
                data.to_csv(f"{self.data_path}{ticker}_historical_data.csv")
                print(f"Dati aggiornati per {ticker}")
            except Exception as e:
                print(f"Failed to download data for {ticker}: {e}")
                self.tickers.remove(ticker)
        print(f"Fine download dati per stocks {self.interval}")

    def download_data_5min(self):
        self.delete_folder_contents(self.data_path)
        print(f"Inizio a scaricare dati per stocks {self.interval}")
        for ticker in self.tickers[:]:
            try:
                data = yf.download(ticker, period="1mo", interval=self.interval)
                data.to_csv(f"{self.data_path}{ticker}_historical_data.csv")
                print(f"Dati aggiornati per {ticker}")
            except Exception as e:
                print(f"Failed to download data for {ticker}: {e}")
                self.tickers.remove(ticker)
        print(f"Fine download dati per stocks {self.interval}")

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

# class StockDataDownloader:
#     def __init__(self, stock_list, interval='1d', index="SP500"):
#         self.tickers = stock_list
#         self.interval = interval
#
#         if interval == '1d' and index == "ALL":
#             self.data_path = f'{source_directory}/Data/ALL/Daily/'
#             self.update_data()
#         elif interval == '1wk' and index == "ALL":
#             self.data_path = f'{source_directory}/Data/ALL/Weekly/'
#         elif interval == '5m' and index == "ALL":
#             self.data_path = f'{source_directory}/Data/ALL/5min/'
#             self.update_data_tf_min()
#         else:
#             raise ValueError("Invalid interval. Choose '1d' for daily or '1wk' for weekly data.")
#
#         if not os.path.exists(self.data_path):
#             os.makedirs(self.data_path)
#
#         self.update_data()
#
#     def clean_data(self, df):
#         """Pulisce il file CSV rimuovendo colonne inutili e formattando i dati correttamente."""
#         try:
#             # Rinomina colonne con tuple
#             df.columns = ['Close', 'High', 'Low', 'Open', 'Volume']
#
#         except Exception as e:
#             print(f"Errore nella pulizia del Df : {e}")
#
#         return df
#
#
#     def download_data(self, ticker):
#         """Scarica e pulisce i dati per un singolo stock."""
#         end_date = datetime.now()
#         start_date = end_date - timedelta(days=2 * 365)
#
#         try:
#             print(f"Scaricamento dati per {ticker}...")
#             data = yf.download(ticker, start=start_date, end=end_date, interval=self.interval)
#             data = self.clean_data(data)
#             data.to_csv(f"{self.data_path}{ticker}_historical_data.csv")
#
#         except Exception as e:
#             print(f"Errore durante il download di {ticker}: {e}")
#
#     def download_data_5min(self, ticker):
#         """Scarica i dati a 5 minuti per un singolo stock e rimuove righe incomplete."""
#         try:
#             print(f"Scaricamento dati a 5 minuti per {ticker}...")
#             data = yf.download(ticker, period="1mo", interval=self.interval)
#             data = self.clean_data(data)
#             data.to_csv(f"{self.data_path}{ticker}_historical_data.csv")
#             print(f"Dati aggiornati per {ticker}")
#         except Exception as e:
#             print(f"Errore durante il download di {ticker}: {e}")
#
#     def update_data(self):
#         """Aggiorna i dati se esistono, altrimenti esegue il download."""
#         end_date = datetime.now()
#
#         for ticker in self.tickers[:]:
#             csv_file = f"{self.data_path}{ticker}_historical_data.csv"
#
#             if not os.path.exists(csv_file):
#                 print(f"{ticker}: dati non trovati, eseguo il download completo.")
#                 if self.interval == '5m':
#                     self.download_data_5min(ticker)
#                 else:
#                     self.download_data(ticker)
#                 continue
#
#             try:
#                 df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
#                 # df = df.rename(columns={'Price': 'Date'})
#
#
#                 if df.empty:
#                     raise Exception("CSV file is empty")
#
#                 last_date = df.index[-1]
#                 last_date = pd.to_datetime(last_date)
#                 start_date = last_date + pd.Timedelta(days=1 if self.interval == '1d' else 7)
#
#                 if start_date < end_date:
#                     print(f"Aggiornamento dati per {ticker}...")
#                     # df = df.rename(columns={'Price': 'Date'})
#                     # df['Date'] = pd.to_datetime(df['Date'])
#
#                     new_data = yf.download(ticker, start=start_date, end=end_date, interval=self.interval)
#                     new_data.columns = ['Close', 'High', 'Low', 'Open', 'Volume']
#                     # # new_data['Date'] = new_data.index
#                     #
#                     # df['Date'] = df.index
#                     # new_data['Date'] = new_data.index
#                     # df.set_index('Date', inplace=True)
#                     # new_data.set_index('Date', inplace=True)
#
#                     combined_df = pd.concat([df, new_data])
#                     combined_df.index = pd.to_datetime(combined_df.index)
#                     combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
#                     combined_df.to_csv(csv_file)
#
#
#                     print(f"Dati aggiornati per {ticker}")
#                 else:
#                     print(f"{ticker} è già aggiornato.")
#
#             except Exception as e:
#                 print(f"Errore con {ticker}: {e}")
#
#     def update_data_tf_min(self):
#         """Aggiorna i dati se esistono, altrimenti esegue il download degli ultimi 2 mesi."""
#         end_date = datetime.now()
#
#         for ticker in self.tickers[:]:
#             csv_file = f"{self.data_path}{ticker}_historical_data.csv"
#
#             # Se il file CSV non esiste, eseguiamo il download degli ultimi 2 mesi
#             if not os.path.exists(csv_file):
#                 print(f"{ticker}: dati non trovati, eseguo il download degli ultimo mese.")
#                 start_date = end_date - timedelta(days=60)  # Gli ultimi 2 mesi
#                 if self.interval == '5m':
#                     self.download_data_5min(ticker)
#                 else:
#                     print(f"Intervallo {self.interval} non implementato per {ticker}.")
#                 continue
#
#             try:
#                 # Carica il CSV esistente
#                 df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
#
#                 if df.empty:
#                     raise Exception("CSV file is empty")
#
#                 # Calcola la data di inizio per l'aggiornamento
#                 last_date = pd.to_datetime(df.index[-1])
#
#                 if last_date.tzinfo is None:
#                     last_date = last_date.tz_localize('UTC')  # Localizza last_date a UTC se è naive
#
#                 # Assicurati che end_date sia UTC
#                 end_date = pd.to_datetime(end_date)
#
#                 if end_date.tzinfo is None:
#                     end_date = end_date.tz_localize('UTC')  # Localizza end_date a UTC se è naive
#
#                 # Calcola la start_date in base all'intervallo
#                 start_date = last_date + pd.Timedelta(minutes=5)
#
#                 # Se ci sono dati nuovi da scaricare
#                 if start_date < end_date:
#                     print(f"Aggiornamento dati per {ticker}...")
#
#                     # Download dei nuovi dati per l'intervallo richiesto
#                     new_data = yf.download(ticker, start=start_date.normalize(), end=end_date.normalize(), interval=self.interval)
#                     new_data = self.clean_data(new_data)
#
#                     # Combina i vecchi e i nuovi dati
#                     combined_df = pd.concat([df, new_data]).drop_duplicates()
#                     combined_df.to_csv(csv_file)
#
#                     # Pulisce il CSV aggiornato
#
#                     print(f"Dati aggiornati per {ticker}")
#                 else:
#                     print(f"{ticker} è già aggiornato.")
#
#             except Exception as e:
#                 print(f"Errore con {ticker}: {e}")
#
#     def delete_folder_contents(self, folder):
#         """Cancella i contenuti di una cartella."""
#         for filename in os.listdir(folder):
#             file_path = os.path.join(folder, filename)
#             try:
#                 if os.path.isfile(file_path) or os.path.islink(file_path):
#                     os.unlink(file_path)
#                 elif os.path.isdir(file_path):
#                     shutil.rmtree(file_path)
#             except Exception as e:
#                 print(f'Failed to delete {file_path}. Reason: {e}')


if __name__ == "__main__":
    stock_list = ["AAPL"]
    downloader = StockDataDownloader(stock_list, interval='5m', index="ALL").download_data_5min()