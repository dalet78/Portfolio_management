import pandas as pd
import mplfinance as mpf
import os
import uuid
from libs.file_checker import FileChecker
import shutil

source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"


class CandlestickChartGenerator:
    def __init__(self, df):
        self.df = df
        # Crea uno stile personalizzato
        self.mpf_style = mpf.make_mpf_style(base_mpf_style='nightclouds',
                                            marketcolors=mpf.make_marketcolors(up='red', down='white', inherit=True),
                                            rc={'figure.facecolor': 'black', 'axes.facecolor': 'black'})
        self.tmp_dir = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/Data/tmp/img"  # Modifica il percorso secondo le tue esigenze
        self.created_files = []  # Lista per tenere traccia dei file creati
        self.check_file = FileChecker()  # Assicurati che FileChecker sia definito correttamente

    def _plot_to_file(self, max_points=None, **kwargs):
        if not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)
        df_to_plot = self.df if max_points is None else self.df[-max_points:]
        temp_file_path = self._generate_temp_file_path()
        # Configura l'asse x per mostrare la data ogni 5 intervalli
        mpf.plot(df_to_plot, type='candlestick', style=self.mpf_style,
                 xrotation=45, datetime_format='%Y-%m-%d',
                 show_nontrading=False, savefig=temp_file_path, **kwargs)
        file_return = self.check_file.wait_for_file_creation(file_path=temp_file_path)
        if file_return:
            self.created_files.append(temp_file_path)
            return temp_file_path
        else:
            print("problem with image creation")
    #
    # def _plot_to_file(self, max_points=None, **kwargs):
    #     if not isinstance(self.df.index, pd.DatetimeIndex):
    #         self.df.index = pd.to_datetime(self.df.index)
    #     df_to_plot = self.df if max_points is None else self.df[-max_points:]
    #     temp_file_path = self._generate_temp_file_path()
    #     mpf.plot(df_to_plot, type='candlestick', style=self.mpf_style, savefig=temp_file_path, **kwargs)
    #     file_return = self.check_file.wait_for_file_creation(file_path=temp_file_path)
    #     if file_return:
    #         self.created_files.append(temp_file_path)  # Aggiungi il percorso del file alla lista
    #         return temp_file_path
    #     else:
    #         print("problem with image creation")

    def _generate_temp_file_path(self):
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)  # Crea la cartella se non esiste
        return os.path.join(self.tmp_dir, f"{uuid.uuid4().hex}.png")

    def create_simple_chart(self, max_points=None):
        return self._plot_to_file(max_points)

    def create_chart_with_horizontal_lines(self, lines, max_points=None):
        add_plots = [mpf.make_addplot([line]*len(self.df[-max_points:]), type='line') for line in lines]
        return self._plot_to_file(max_points, addplot=add_plots)

    def create_chart_with_horizontal_lines_and_volume(self, lines, max_points=None):
        # Preparazione dei dati per il grafico delle linee orizzontali
        add_plots = [mpf.make_addplot([line] * len(self.df[-max_points:]), type='line') for line in lines]

        # Aggiunta del grafico del volume
        volume_plot = mpf.make_addplot(self.df['Volume'][-max_points:], type='bar', panel=1, color='blue', alpha=0.5)
        add_plots.append(volume_plot)

        # Creazione del grafico con mplfinance
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

    def create_chart_with_RSI(self, period=14, max_points=None, file_name='rsi_chart.png'):
        # Calcolo dell'RSI
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Troncare i dati per il numero massimo di punti se specificato
        df_to_plot = self.df if max_points is None else self.df[-max_points:]
        rsi_to_plot = rsi if max_points is None else rsi[-max_points:]

        # Preparazione dell'addplot per RSI
        apd = mpf.make_addplot(rsi_to_plot, type='line', secondary_y=True)

        # Uso della funzione _plot_to_file per creare il grafico
        return self._plot_to_file(max_points, addplot=apd)

    def create_chart_with_EMA(self, period=20, max_points=None):
        ema = self.df['Close'].ewm(span=period, adjust=False).mean()
        return self._plot_to_file(max_points, addplot=mpf.make_addplot(ema))

    def create_chart_with_MACD(self, short_period=12, long_period=26, signal_period=9, max_points=None):
        # Calcolo delle EMA a breve e lungo termine
        ema_short = self.df['Close'].ewm(span=short_period, adjust=False).mean()
        ema_long = self.df['Close'].ewm(span=long_period, adjust=False).mean()

        # Calcolo del MACD e del segnale MACD
        macd = ema_short - ema_long
        macd_signal = macd.ewm(span=signal_period, adjust=False).mean()

        # Troncare i dati per il numero massimo di punti se specificato
        df_to_plot = self.df if max_points is None else self.df[-max_points:]
        macd_to_plot = macd if max_points is None else macd[-max_points:]
        macd_signal_to_plot = macd_signal if max_points is None else macd_signal[-max_points:]

        # Preparazione dell'addplot per MACD e il segnale MACD
        apd_macd = mpf.make_addplot(macd_to_plot, type='bar', panel=1, color='dimgray', secondary_y='auto')
        apd_signal = mpf.make_addplot(macd_signal_to_plot, type='line', panel=1, color='fuchsia', secondary_y='auto')

        # Specifica il rapporto tra i pannelli
        panel_ratios = (1, 0.5)  # Ad esempio, il pannello MACD è la metà dell'altezza del pannello principale

        # Uso della funzione _plot_to_file per creare il grafico
        return self._plot_to_file(max_points, addplot=[apd_macd, apd_signal], panel_ratios=panel_ratios)
    
    def create_chart_with_areas(self, market_profile, vwap_values, max_points=None):
        """
        Crea un grafico che mostra le aree di Market Profile e VWAP.

        :param market_profile: Dizionario con i valori di VAL, POC, VAH per Market Profile.
        :param vwap_values: Dizionario con i valori di VAL, POC, VAH per VWAP.
        :param max_points: Numero massimo di punti da visualizzare.
        """
        # Assicurati che df sia indicizzato correttamente
        if not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)

        # Tronca il DataFrame se necessario
        df_to_plot = self.df if max_points is None else self.df[-max_points:]

        # Creazione delle aree per Market Profile e VWAP
        mp_area = [market_profile['VAL'], market_profile['POC'], market_profile['VAH']]
        vwap_area = [vwap_values['VAL'], vwap_values['POC'], vwap_values['VAH']]

        # Aggiungi le linee orizzontali per le aree
        # Aggiungi le linee orizzontali per le aree e crea le legende
        colors = ['green', 'blue', 'red', 'purple', 'orange', 'brown']

        # Aggiungi le linee orizzontali per le aree, usando un colore diverso per ciascuna
        add_plots = []
        i = 0  # indice per i colori

        for label, line in market_profile.items():
            add_plots.append(mpf.make_addplot([line] * len(df_to_plot), type='line', linestyle='dashdot',
                                              color=colors[i % len(colors)], label=f'Market {label}'))
            i += 1

        for label, line in vwap_values.items():
            add_plots.append(mpf.make_addplot([line] * len(df_to_plot), type='line', linestyle='dashdot',
                                              color=colors[i % len(colors)], label=f'VWAP {label}'))
            i += 1

        temp_file_path = self._generate_temp_file_path()
        # Creazione e salvataggio del grafico
        mpf.plot(df_to_plot, type='candlestick', style=self.mpf_style,
                 addplot=add_plots, title='Stock Analysis', ylabel='Price', savefig=temp_file_path)
        #
        # add_plots = [mpf.make_addplot([line]*len(df_to_plot), type='line') for line in mp_area + vwap_area]
        #
        # # Creazione e salvataggio del grafico
        #
        # mpf.plot(df_to_plot, type='candlestick', style=self.mpf_style,
        #          addplot=add_plots, savefig=temp_file_path)
        return temp_file_path
        
    def clear_temp_files(self):
        for item in os.listdir(self.tmp_dir):
            item_path = os.path.join(self.tmp_dir, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)  # Rimuove file o link simbolici
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
