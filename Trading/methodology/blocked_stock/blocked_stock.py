from Reports.report_builder import ReportGenerator
from Reports.image_builder import CandlestickChartGenerator
import json
import pandas as pd
from libs.filtered_stock import return_filtred_list
import time


class TradingAnalyzer:
    def __init__(self, dataset):
        """
        Initialize the TradingAnalyzer with a stock dataset.
        :param dataset: List of stock prices (float).
        """
        self.dataset = dataset
        self.image = CandlestickChartGenerator(self.dataset)

    def get_last_value(self, dataset_subset=None):
        """
        Get the last value from the dataset or a subset of it.
        :param dataset_subset: Optional subset of the dataset to consider. If None, uses the entire dataset.
        :return: The last stock price in the dataset or subset.
        """
        # Utilizza il subset del dataset se fornito, altrimenti utilizza l'intero dataset
        dataset_to_use = dataset_subset if dataset_subset is not None else self.dataset

        if not dataset_to_use.empty:
            return dataset_to_use["Close"].iloc[-1]
        return None

    def calculate_support_resistance(self, price):
        """
        Calculate support and resistance levels based on the given price.
        :param price: The stock price.
        :return: A tuple of (support, resistance).
        """
        resistance = int(price) + 1 if price and not pd.isna(price) else None
        support = int(price) if price and not pd.isna(price) else None
        return support, resistance

    def check_signal(self, period=30):
        """
        Check if the stock price remains below resistance for more than 30 sessions and count how many times it touches or comes close to resistance within a 1% margin. Then do the opposite for support.
        If 'use_previous_day' is True, considers the dataset starting from the previous day.
        :param period: The number of periods to check.
        :param use_previous_day: Boolean to consider the dataset from the previous day.
        :return: A dictionary with details of price interactions with support and resistance.
        """
        dataset_to_use = self.dataset

        if len(dataset_to_use) < period:
            return False, None, None

        if not isinstance(dataset_to_use.index, pd.DatetimeIndex):
            dataset_to_use['Date'] = pd.to_datetime(dataset_to_use['Date'])
            dataset_to_use.set_index('Date', inplace=True)

        # trade_date = dataset_to_use.index[-1].strftime('%Y-%m-%d')
        dataset_to_use['support'] = [self.calculate_support_resistance(dataset_to_use['Close'].iloc[i])[0] for i in
                                     range(len(dataset_to_use))]
        dataset_to_use['resistance'] = [self.calculate_support_resistance(dataset_to_use['Close'].iloc[i])[1] for i in
                                        range(len(dataset_to_use))]

        # Aggiunta delle colonne is_interesting e signal
        dataset_to_use['is_interesting'] = 0
        dataset_to_use['signal'] = 0

        dataset_to_use = self.calculate_interesting_parameter(dataset_to_use, period)

        dataset_to_use = self.calculate_interesting_column(dataset_to_use)

        # Calcolo del signal in base alle ultime condizioni di is_interesting
        dataset_to_use = self.get_signal(dataset_to_use)
        result, image = self.analyze_interesting_data(dataset_to_use, period)

        return result, image, dataset_to_use

    def calculate_interesting_parameter(self, dataset_to_use, period):
        support_resistence_col, sup_res_gap_touch_count, sup_res_touch_count= [],[],[]
        for i in range(len(dataset_to_use) - 1, period - 2, -1):
            # current_close = dataset_to_use['Close'].iloc[i]
            current_support = dataset_to_use['support'].iloc[i]
            current_resistance = dataset_to_use['resistance'].iloc[i]
            df_segment = dataset_to_use.iloc[i-period+1:i+1]
            support_resistence_verify = self.check_support_resistance_break(
                                        df=df_segment,
                                        support_value=current_support,
                                        resistance_value=current_resistance
                                    )
            sup_res_approach_count_list= self.check_hloc_proximity(df=df_segment,
                                        support_value=current_support,
                                        resistance_value=current_resistance)
            sup_res_gap_touch_count_list= self.check_hloc_proximity_with_gap(df=df_segment,
                                        support_value=current_support,
                                        resistance_value=current_resistance)
            
            support_resistence_col.append(support_resistence_verify)
            sup_res_touch_count.append(sup_res_approach_count_list)
            sup_res_gap_touch_count.append(sup_res_gap_touch_count_list)

        nan_list = [pd.NA] * (period - 1)
        support_resistence_col_r = list(reversed(support_resistence_col))
        sup_res_touch_count_r = list(reversed(sup_res_touch_count))
        sup_res_gap_touch_count_r = list(reversed(sup_res_gap_touch_count))
        #dataset_to_use['support_resistence_col'] = [val for val in support_resistence_col for _ in range(20)][:len(dataset_to_use)]
        dataset_to_use['support_resistence_col']= nan_list + support_resistence_col_r
        dataset_to_use['sup_res_approach_count_approx']= nan_list + sup_res_touch_count_r
        dataset_to_use['sup_res_gap_touch']= nan_list + sup_res_gap_touch_count_r
        dataset_to_use = dataset_to_use.dropna()
        return dataset_to_use

    def analyze_interesting_data(self, dataset_to_use, period):
        """
        Analizza i dati per 'is_interesting' e genera i dettagli e un grafico corrispondente.

        Args:
        dataset_to_use (pd.DataFrame): DataFrame contenente i dati di interesse.
        period (int): Il periodo da considerare per la generazione del grafico.

        Returns:
        tuple: Una tupla contenente un dizionario con i risultati e un'immagine del grafico.
        """
        last_row = dataset_to_use.iloc[-1]
        if last_row['is_interesting'] != 0:
            print(last_row)
        if dataset_to_use['is_interesting'].iloc[-1] == 1:
            previous_support = dataset_to_use['support'].iloc[-1]
            image = self.image.create_chart_with_horizontal_lines(lines=[int(previous_support)], max_points=period+10)
            result = {
                "status": "above_support",
                "details": {
                    "support": previous_support,
                    "enter_price": previous_support - 0.10,
                    "stop_loss": previous_support + 0.20,
                    "take_profit": previous_support - 0.50
                }
            }
        elif dataset_to_use['is_interesting'].iloc[-1] == 2:
            previous_resistance = dataset_to_use['resistance'].iloc[-1]
            image = self.image.create_chart_with_horizontal_lines(lines=[int(previous_resistance)], max_points=period+10)
            result = {
                "status": "below_resistance",
                "details": {
                    "resistance": previous_resistance,
                    "enter_price": previous_resistance + 0.10,
                    "stop_loss": previous_resistance - 0.20,
                    "take_profit": previous_resistance + 0.50
                }
            }
        elif dataset_to_use['is_interesting'].iloc[-1] == 3:
            previous_support = dataset_to_use['support'].iloc[-1]
            previous_resistance = dataset_to_use['resistance'].iloc[-1]
            image = self.image.create_chart_with_more_horizontal_lines(lines=[int(previous_support), int(previous_resistance)],
                                                                       max_points=period+10)
            result = {
                "status": "both_support_and_resistance",
                "details": {
                    "support": previous_support,
                    "resistance": previous_resistance,
                    # Aggiungi ulteriori dettagli se necessario
                }
            }
        else:
            result = None
            image = None
        return result, image
    
    def calculate_interesting_column(self, dataset_to_use):
        for i, row in dataset_to_use.iterrows():
            if (row['support_resistence_col'] == 3) and (row['sup_res_approach_count_approx'] == 3 or row['sup_res_gap_touch'] == 3):
                dataset_to_use.at[i, 'is_interesting'] = 3
            elif row['support_resistence_col'] == 1 and (row['sup_res_gap_touch'] == 1 or row['sup_res_approach_count_approx'] == 1):
                dataset_to_use.at[i, 'is_interesting'] = 1
            elif row['support_resistence_col'] == 2 and (row['sup_res_gap_touch'] == 2 or row['sup_res_approach_count_approx'] == 2):
                dataset_to_use.at[i, 'is_interesting'] = 2
            else:
                dataset_to_use.at[i, 'is_interesting'] = 0
        return dataset_to_use

    def clear_img_temp_files(self):
        self.image.clear_temp_files()

    def get_signal(self, dataset_to_use):
        """
        Calcola i valori della colonna 'signal' basandosi sulle condizioni date.

        Args:
        dataset_to_use (pd.DataFrame): DataFrame contenente i dati di interesse.

        Returns:
        pd.DataFrame: DataFrame modificato con la colonna 'signal' aggiunta o aggiornata.
        """
        for i in range(1, len(dataset_to_use)):
            last_is_interesting = dataset_to_use.loc[dataset_to_use.index[i - 1], 'is_interesting']
            previous_support = dataset_to_use.loc[dataset_to_use.index[i - 1], 'support']
            previous_resistance = dataset_to_use.loc[dataset_to_use.index[i - 1], 'resistance']
            if last_is_interesting == 1:
                # Condizioni per signal = 1 con il supporto del giorno precedente
                if any([
                    dataset_to_use['High'].iloc[i] < previous_support - 0.10,
                    dataset_to_use['Low'].iloc[i] < previous_support - 0.10,
                    dataset_to_use['Open'].iloc[i] < previous_support - 0.10,
                    dataset_to_use['Close'].iloc[i] < previous_support - 0.10
                ]):
                    dataset_to_use.at[i, 'signal'] = 1
            elif last_is_interesting == 2:
                # Condizioni per signal = 2 con la resistenza del giorno precedente
                if any([
                    dataset_to_use['High'].iloc[i] > previous_resistance + 0.10,
                    dataset_to_use['Low'].iloc[i] > previous_resistance + 0.10,
                    dataset_to_use['Open'].iloc[i] > previous_resistance + 0.10,
                    dataset_to_use['Close'].iloc[i] > previous_resistance + 0.10
                ]):
                    dataset_to_use.at[i, 'signal'] = 2
            elif last_is_interesting == 3:
                # Condizioni per signal = 1 o 2 quando entrambi supporto e resistenza sono interessanti
                if any([
                    dataset_to_use['High'].iloc[i] < previous_support - 0.10,
                    dataset_to_use['Low'].iloc[i] < previous_support - 0.10,
                    dataset_to_use['Open'].iloc[i] < previous_support - 0.10,
                    dataset_to_use['Close'].iloc[i] < previous_support - 0.10
                ]):
                    dataset_to_use.at[i, 'signal'] = 1
                elif any([
                    dataset_to_use['High'].iloc[i] > previous_resistance + 0.10,
                    dataset_to_use['Low'].iloc[i] > previous_resistance + 0.10,
                    dataset_to_use['Open'].iloc[i] > previous_resistance + 0.10,
                    dataset_to_use['Close'].iloc[i] > previous_resistance + 0.10
                ]):
                    dataset_to_use.at[i, 'signal'] = 2
            return dataset_to_use

    def check_support_resistance_break(self, df, support_value, resistance_value, columns=['Open', 'Close', 'High', 'Low']):
        """
        Verifica se il supporto o la resistenza sono stati violati in un dato periodo.

        Args:
        df (pd.DataFrame): DataFrame contenente le colonne HLOC.
        period (int): Numero di periodi da considerare.
        current_support (float): Valore corrente del supporto.
        current_resistance (float): Valore corrente della resistenza.
        start_index (int): Indice di partenza per il controllo.

        Returns:
        (bool, bool): Tuple dove il primo valore indica se il supporto è stato rotto,
                      e il secondo valore indica se la resistenza è stata rotta.
        """
        #controlla le soglie
        if ((df[columns] > support_value) & (df[columns] < resistance_value)).all(axis=None):
            return 3
        # Controlla se tutti i valori sono sopra la soglia inferiore
        elif (df[columns] > support_value).all(axis=None):
            return 1
        # Controlla se tutti i valori sono sotto la soglia superiore
        elif (df[columns] < resistance_value).all(axis=None):
            return 2
        else:
            return 0

    def check_hloc_proximity(self, df, resistance_value, support_value, approximation=0.02):
        """
        Verifica se High/Low del DataFrame tocca la resistenza/supporto per tre volte consecutive.

        Args:
        df (pd.DataFrame): DataFrame contenente le colonne HLOC.
        resistance_value (float): Valore di riferimento per la resistenza.
        support_value (float): Valore di riferimento per il supporto.
        approximation (float): Percentuale di approssimazione (default 2%).

        Returns:
        int: 3 se tocca sia resistenza che supporto, 2 se tocca solo resistenza,
            1 se tocca solo supporto, 0 altrimenti.
        """
        lower_resistance = resistance_value * (1 - approximation)
        upper_resistance = resistance_value * (1 + approximation)
        lower_support = support_value * (1 - approximation)
        upper_support = support_value * (1 + approximation)

        resistance_count = 0
        support_count = 0

        for index, row in df.iterrows():
            # Controlla la resistenza
            if lower_resistance <= row['High'] <= upper_resistance:
                resistance_count += 1
            else:
                resistance_count = 0

            # Controlla il supporto
            if lower_support <= row['Low'] <= upper_support:
                support_count += 1
            else:
                support_count = 0

            # Verifica le condizioni
            if resistance_count >= 3 and support_count >= 3:
                return 3
            elif resistance_count >= 3:
                return 2
            elif support_count >= 3:
                return 1

        return 0

    def check_hloc_proximity_with_gap(self, df, resistance_value, support_value, approximation=0.02, min_gap=3):
        """
        Verifica se un valore HLOC si avvicina alla resistenza e/o al supporto
        almeno due volte, con almeno tre righe di differenza tra queste occorrenze.

        Args:
        df (pd.DataFrame): DataFrame contenente le colonne HLOC.
        resistance_value (float): Valore di riferimento per la resistenza.
        support_value (float): Valore di riferimento per il supporto.
        approximation (float): Percentuale di approssimazione (default 2%).
        min_gap (int): Numero minimo di righe di differenza tra le occorrenze.

        Returns:
        int: 3 per contatti sia con resistenza che supporto, 2 solo resistenza,
            1 solo supporto, 0 altrimenti.
        """
        lower_resistance = resistance_value * (1 - approximation)
        upper_resistance = resistance_value * (1 + approximation)
        lower_support = support_value * (1 - approximation)
        upper_support = support_value * (1 + approximation)

        last_resistance_pos = None
        resistance_touch_count = 0

        last_support_pos = None
        support_touch_count = 0

        for index, row in df.iterrows():
            current_pos = df.index.get_loc(index)

            # Controlla la resistenza
            if lower_resistance <= row['High'] <= upper_resistance:
                if last_resistance_pos is not None and (current_pos - last_resistance_pos) >= min_gap:
                    resistance_touch_count += 1
                last_resistance_pos = current_pos

            # Controlla il supporto
            if lower_support <= row['Low'] <= upper_support:
                if last_support_pos is not None and (current_pos - last_support_pos) >= min_gap:
                    support_touch_count += 1
                last_support_pos = current_pos

            if resistance_touch_count >= 2 and support_touch_count >= 2:
                return 3
            elif resistance_touch_count >= 2:
                return 2
            elif support_touch_count >= 2:
                return 1

        return 0



def main(index="Russel"):
    start_time = time.time()  # Registra l'ora di inizio
    source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
    report = ReportGenerator()
    report.add_title(title=f"{index} Report blocked stock")

    with open(f"{source_directory}/Trading/methodology/strategy_parameter.json", 'r') as file:
        param_data = json.load(file)

    tickers_list = return_filtred_list(index=index)
    # Controlla se la lista dei ticker è vuota
    if not tickers_list:
        # Aggiungi un messaggio nel report o registra un log
        report.add_content("Nessun ticker soddisfa i criteri di selezione.")
        print("Nessun ticker soddisfa i criteri di selezione.")
    else:

        for item in tickers_list:
            try:
                data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv",
                                   parse_dates=['Date'])
                data = data.tail(60)
                enhanced_strategy = TradingAnalyzer(data)
                print(f'stock = {item}')
                result, image, new_data = enhanced_strategy.check_signal(period=20)
                # filtred_interesting_dataset =new_data[new_data['is_interesting'] != 0]
                # count_interesting = filtred_interesting_dataset['is_interesting'].count()
                # filtred_signal_dataset = new_data[new_data['signal'] != 0]
                # count_signal = filtred_signal_dataset['signal'].count()
                if result:
                    report.add_content(f'stock = {item} \n')
                    report.add_commented_image(df=data, comment=f'Description = {result["details"]}', image_path=image)
                # if not filtred_interesting_dataset.empty:
                #     report.add_content(f'stock = {item} \n count interesting= {count_interesting}\n')
                #     report.add_content(f'stock = {item} \n count signal= {count_signal}\n')
                last_signal = new_data['signal'].iloc[-1]
                if last_signal == 1:
                    print(f"Segnale di vendita (sell) per {item}")
                    # Aggiungi logica per gestire il segnale di vendita
                elif last_signal == 2:
                    print(f"Segnale di acquisto (buy) per {item}")
                    # Aggiungi logica per gestire il segnale di acquisto

            except FileNotFoundError:
                # Gestisci l'errore se il file non viene trovato
                print(f"File non trovato per {item}")
            except Exception as e:
                # Gestisci altri errori generici
                print(f"Errore durante l'elaborazione di {item}: {e}")

        # Salva il report e pulisci i file temporanei
    file_report = report.save_report(filename=f"{index}_Report_blocked_stock")
    enhanced_strategy.clear_img_temp_files()
    end_time = time.time()  # Registra l'ora di fine
    duration = end_time - start_time  # Calcola la durata totale

    print(f"Tempo di elaborazione {index}: {duration} secondi.")

    return file_report


if __name__ == '__main__':
    file_report = main()
    print(file_report)
