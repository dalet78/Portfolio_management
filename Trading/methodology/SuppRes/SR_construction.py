import pandas as pd
import numpy as np
import os

class StockAnalysis:
    def __init__(self, csv_file, interval='1d'):
        self.interval = interval
        data_path = 'Trading/Data/'

        if interval == '1d':
            data_path += 'Daily/'
        elif interval == '1wk':
            data_path += 'Weekly/'
        else:
            raise ValueError("Invalid interval. Choose '1d' for daily or '1wk' for weekly data.")

        self.data = pd.read_csv(f'{data_path}{csv_file}_historical_data.csv')
        self.support_resistance_levels = {}
        self.filepath = f'Trading/Data/SuppResist/{csv_file}_SR.csv'

        # Assicurati che la cartella esista per il file di output
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def identify_pivots(self, close_prices, thresholds=(25, 50, 75), days=(7, 5, 3)):
        pivots = []
        for i in range(max(days), len(close_prices) - max(days)):
            # Determinare il numero di giorni da considerare in base al prezzo
            if close_prices.iloc[i] < thresholds[0]:
                day_range = days[0]
            elif close_prices.iloc[i] < thresholds[1]:
                day_range = days[1]
            elif close_prices.iloc[i] < thresholds[2]:
                day_range = days[2]
            else:
                day_range = days[-1]  # Usa 3 giorni per prezzi superiori a 75

            max_range = close_prices[i-day_range:i+day_range+1]
            min_range = close_prices[i-day_range:i+day_range+1]

            if close_prices.iloc[i] == max_range.max():
                pivots.append(close_prices.iloc[i])
            elif close_prices.iloc[i] == min_range.min():
                pivots.append(close_prices.iloc[i])
        
        return pivots
    
    def _round_to_nearest(self, value, tick_size):
        # Arrotonda il valore al multiplo di tick_size più vicino
        return round(value / tick_size) * tick_size

    # def _group_and_normalize_pivots(self, pivots):
        # # Raggruppamento e arrotondamento dei Pivot
        # pivot_groups = {}
        # for pivot in pivots:
        #     found_group = False
        #     for key in pivot_groups.keys():
        #         if np.isclose(pivot, key, atol=pivot*0.01):
        #             pivot_groups[key].append(pivot)
        #             found_group = True
        #             break
        #     if not found_group:
        #         pivot_groups[pivot] = [pivot]

        # # rounded_pivots = {round(np.mean(v), 2): len(v) for k, v in pivot_groups.items()}
        # rounded_pivots = {self._round_to_nearest(np.mean(v), 0.05): len(v) for k, v in pivot_groups.items()}

        # # Normalizzazione dei pesi
        # max_weight = max(rounded_pivots.values())
        # normalized_pivots = {k: int(10 * v / max_weight) for k, v in rounded_pivots.items()}

        # return normalized_pivots
        # Raggruppamento dei Pivot Vicini
    def _group_and_normalize_pivots(self, pivots, close_prices):
        pivot_groups = {}
        for pivot in pivots:
            found_group = False
            for key in pivot_groups.keys():
                if abs(pivot - key) / key < 0.01:  # Ad esempio, 1% di differenza
                    pivot_groups[key].append(pivot)
                    found_group = True
                    break
            if not found_group:
                pivot_groups[pivot] = [pivot]

        # Calcolare la Frequenza di Contatto
        contact_freq = {k: 0 for k in pivot_groups}
        for price in close_prices:
            for pivot in pivot_groups:
                if abs(price - pivot) / pivot < 0.01:  # Utilizzando la stessa soglia di percentuale
                    contact_freq[pivot] += 1

        # Calcolare i Pesi
        max_freq = max(contact_freq.values())
        pivot_weights = {self._round_to_nearest(np.mean(v), 0.5): contact_freq[k]/max_freq * 10 
                         for k, v in pivot_groups.items()}

        return pivot_weights
    

    def calculate_support_resistance(self):
        # Assicurarsi che i dati siano disponibili
        if self.data.empty:
            return

        close_prices = self.data['Close']

        # Identificazione dei Pivot
        pivots = self.identify_pivots(close_prices)

        # Raggruppamento e normalizzazione dei Pivot
        # support_resistance_levels = self._group_and_normalize_pivots(pivots, close_prices)
        
        # Calcolare la Media Mobile
        window_size = 20  # Ad esempio, una media mobile di 20 giorni
        self.data['SMA'] = self.data['Close'].rolling(window=window_size).mean()

        # Identificare i Pivot
        pivots = self.identify_pivots(self.data['Close'])

        # Filtrare i Pivot in Base alla Media Mobile
        filtered_pivots = []
        for pivot in pivots:
            pivot_index = self.data[self.data['Close'] == pivot].index[0]
            if abs(pivot - self.data.loc[pivot_index, 'SMA']) / self.data.loc[pivot_index, 'SMA'] < 0.01:  # Ad esempio, entro l'1% della SMA
                filtered_pivots.append(pivot)

        # Raggruppare e Normalizzare i Pivot
        pivot_weights = self._group_and_normalize_pivots(filtered_pivots, self.data['Close'])

        return pivot_weights

    def assign_weight(self, level):
        # Implementare la logica per calcolare il peso in base al numero di volte
        # in cui il livello è stato raggiunto
        pass

    def find_max_min(self):
        if self.data.empty:
            return {}

        # Inizializzazione dei dizionari per i massimi e i minimi
        max_prices = {}
        min_prices = {}

        # Calcolare il massimo e il minimo per ogni colonna rilevante e arrotondare
        for column in ['Open', 'High', 'Low', 'Close']:
            max_price = self.data[column].max()
            min_price = self.data[column].min()

            max_price_rounded = self._round_to_nearest(max_price, 0.05)
            min_price_rounded = self._round_to_nearest(min_price, 0.05)

            max_prices[column] = max_price_rounded
            min_prices[column] = min_price_rounded

        # Ottenere il massimo dei massimi e il minimo dei minimi
        overall_max = max(max_prices.values())
        overall_min = min(min_prices.values())

        # Restituire solo il massimo e il minimo più recenti
        return {overall_max: 10, overall_min: 10}

    def get_support_resistance_levels(self):
        support_resistance_levels = self.calculate_support_resistance()

        # Aggiungere max e min
        max_min_levels = self.find_max_min()
        for level, weight in max_min_levels.items():
            if level not in support_resistance_levels:
                support_resistance_levels[level] = weight

        # Ordina il dizionario
        ordered_levels = sorted(support_resistance_levels.items())

        return ordered_levels

    def update_pivot_data(self):
        # Calcolare i nuovi livelli di supporto e resistenza
        new_pivot_data = self.get_support_resistance_levels()

        try:
            # Provare a leggere il file esistente
            existing_data = pd.read_csv(self.filepath)

            # Convertire i nuovi dati in un DataFrame per il confronto
            new_data_df = pd.DataFrame(new_pivot_data, columns=['Level', 'Weight'])

            # Confrontare i nuovi dati con quelli esistenti
            if not new_data_df.equals(existing_data):
                # Se ci sono nuovi dati, aggiornare il file
                new_data_df.to_csv(self.filepath, index=False)
                print(f"Pivot data updated in {self.filepath}")
            else:
                print("No new pivot data to update.")

        except FileNotFoundError:
            # Se il file non esiste, salvarlo per la prima volta
            self.save_pivot_data(self.filepath)
    
    def save_pivot_data(self,csv_file_name):
        support_resistance_levels = self.get_support_resistance_levels()
        pivot_data = pd.DataFrame(support_resistance_levels, columns=['Level', 'Weight'])

        # Salvare in un file CSV
        pivot_data.to_csv(f"{self.filepath}", index=False)
        print(f"Pivot data saved to {self.filepath}")


#     def plot_support_resistance(self):
#         if self.data.empty:
#             return

#         # Convertire l'indice in DatetimeIndex se necessario
#         if not isinstance(self.data.index, pd.DatetimeIndex):
#             self.data['Date'] = pd.to_datetime(self.data['Date'])
#             self.data.set_index('Date', inplace=True)

#         # Filtrare i dati per gli ultimi 2 anni
#         start_date = datetime.now() - timedelta(days=2*365)
#         recent_data = self.data[start_date:]

#         # Calcolare i livelli di supporto e resistenza
#         support_resistance_levels = self.get_support_resistance_levels()

#         # Creare un grafico a candele per gli ultimi 2 anni
#         # Creare il grafico a candele con dimensioni raddoppiate
#         # fig, axes = mpf.plot(recent_data, type='candle', style='charles',
#         #                      title="Candlestick Chart con Supporti e Resistenze (Ultimi 5 Anni)",
#         #                      mav=(20), volume=False, show_nontrading=True, returnfig=True, figsize=(24, 16))
#         fig, ax = mpf.plot(self.data, type='candle', style='charles',
#                            title="Candlestick Chart con Supporti e Resistenze",
#                            mav=(20), volume=False, show_nontrading=True, returnfig=True, figsize=(24, 16))

#         cmap = plt.get_cmap('coolwarm')

#         # Aggiungere le linee di supporto e resistenza con colori variabili
#         for level, weight in support_resistance_levels:
#             color = cmap(weight / 10)  # Normalizza il peso per il colore
#             ax[0].axhline(y=level, color=color, linewidth=1)  # Usa un linewidth ridotto
#             ax[0].text(self.data.index[-1], level, f'{level}', verticalalignment='center', color=color)

#         plt.savefig('portfolio_management/Trading/testing/stock_analysis_chart.png', dpi=100)


# stock_analysis = StockAnalysis(csv_file="A", interval= "1wk")
# support_resistance_levels = stock_analysis.calculate_support_resistance()
# print(support_resistance_levels)
# stock_analysis.plot_support_resistance()