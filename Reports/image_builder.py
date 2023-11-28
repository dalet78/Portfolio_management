import pandas as pd
import mplfinance as mpf
import os
import uuid
from portfolio_management.libs.file_checker import FileChecker
import shutil

class CandlestickChartGenerator:
    def __init__(self, df):
        self.df = df
        self.mpf_style = mpf.make_mpf_style(base_mpf_style='nightclouds', rc={'figure.facecolor': 'black', 'axes.facecolor': 'black'})
        self.tmp_dir = "portfolio_management/Reports/Data/tmp/img"
        self.created_files = []  # Lista per tenere traccia dei file creati
        self.check_file= FileChecker()

    def _plot_to_file(self, max_points=None, **kwargs):
        if not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)
        df_to_plot = self.df if max_points is None else self.df[-max_points:]
        temp_file_path = self._generate_temp_file_path()
        mpf.plot(df_to_plot, type='candlestick', style=self.mpf_style, savefig=temp_file_path, **kwargs)
        file_return = self.check_file.wait_for_file_creation(file_path=temp_file_path)
        if file_return:
            self.created_files.append(temp_file_path)  # Aggiungi il percorso del file alla lista
            return temp_file_path
        else: 
            print("problem with image creation")

    def _generate_temp_file_path(self):
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)  # Crea la cartella se non esiste
        return os.path.join(self.tmp_dir, f"{uuid.uuid4().hex}.png")

    def create_simple_chart(self, max_points=None):
        return self._plot_to_file(max_points)

    def create_chart_with_horizontal_lines(self, lines, max_points=None):
        add_plots = [mpf.make_addplot([line]*len(self.df[-max_points:]), type='line') for line in lines]
        return self._plot_to_file(max_points, addplot=add_plots)

    def create_chart_with_more_horizontal_lines(self, lines, max_points=None):
        # Assicurati che 'lines' sia una lista di valori
        if not isinstance(lines, list):
            raise ValueError("L'argomento 'lines' deve essere una lista.")

        # Crea una lista di 'make_addplot' per ogni linea in 'lines'
        add_plots = [mpf.make_addplot([line] * len(self.df[-max_points:]), type='line') for line in lines]
        
        # Chiamata alla funzione interna per creare e salvare il grafico
        return self._plot_to_file(max_points, addplot=add_plots)

    def create_chart_with_SMA(self, period=20, max_points=None):
        sma = self.df['Close'].rolling(window=period).mean()
        return self._plot_to_file(max_points, addplot=mpf.make_addplot(sma))

    def create_chart_with_EMA(self, period=20, max_points=None):
        ema = self.df['Close'].ewm(span=period, adjust=False).mean()
        return self._plot_to_file(max_points, addplot=mpf.make_addplot(ema))

    def clear_temp_files(self):
        for item in os.listdir(self.tmp_dir):
            item_path = os.path.join(self.tmp_dir, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)  # Rimuove file o link simbolici
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
# df=pd.read_csv(f'portfolio_management/Trading/Data/Daily/MMM_historical_data.csv')
# img = CandlestickChartGenerator(df)
# img_path = img.create_simple_chart()
# print(img_path)

# import pandas as pd
# import mplfinance as mpf
# import matplotlib.pyplot as plt
# import io
# from PIL import Image
# import tempfile

# class CandlestickChartGenerator:
#     def __init__(self, df):
#         self.df = df
#         self.mpf_style = {'backgroundcolor': 'black',
#                           'facecolor': 'black',
#                           'gridstyle': 'dashed',
#                           'gridcolor': '#808080'}
#         self.buffer = None

#     def _plot_to_buffer(self, max_points=None, **kwargs):
#     # Assicurati che l'indice sia un DatetimeIndex
#         if not isinstance(self.df.index, pd.DatetimeIndex):
#             # Converti l'indice in DatetimeIndex qui
#             self.df.index = pd.to_datetime(self.df.index)
#         df_to_plot = self.df if max_points is None else self.df[-max_points:]
#         mpf_style = mpf.make_mpf_style(base_mpf_style='nightclouds', rc={'figure.facecolor': 'black', 'axes.facecolor': 'black'})
#         self.buffer = io.BytesIO()
#         mpf.plot(df_to_plot, type='candlestick', style=mpf_style, savefig=dict(fname=self.buffer, format='png'), **kwargs)
#         self.buffer.seek(0)
#         return self.buffer

#     def create_simple_chart(self, max_points=None):
#          return Image.open(self._plot_to_buffer(max_points))

#     def create_chart_with_horizontal_lines(self, lines, max_points=None):
#         buffer = self._plot_to_buffer(max_points, addplot=[mpf.make_addplot([line]*len(self.df[-max_points:]), type='line') for line in lines])
#         # Salva il grafico in un file temporaneo
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
#             tmp_file.write(buffer.read())
#             return tmp_file.name 

#     def create_chart_with_SMA(self, period=20, max_points=None):
#         sma = self.df['Close'].rolling(window=period).mean()
#         add_plot = mpf.make_addplot(sma)
#         return Image.open(self._plot_to_buffer(max_points, addplot=add_plot))

#     def create_chart_with_EMA(self, period=20, max_points=None):
#         ema = self.df['Close'].ewm(span=period, adjust=False).mean()
#         add_plot = mpf.make_addplot(ema)
#         return Image.open(self._plot_to_buffer(max_points, addplot=add_plot))

#     def clear_buffer(self):
#         if self.buffer:
#             self.buffer.close()
#             self.buffer = None

