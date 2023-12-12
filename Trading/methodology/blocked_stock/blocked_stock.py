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
            # Se l'indice non è del tipo DateTimeIndex, prova a convertirlo
            # Assicurati che ci sia una colonna che possa essere convertita in un indice di date
            # Ad esempio, se hai una colonna 'Date' nel DataFrame
            dataset_to_use['Date'] = pd.to_datetime(dataset_to_use['Date'])
            dataset_to_use.set_index('Date', inplace=True)

        trade_date = dataset_to_use.index[-1].strftime('%Y-%m-%d')
        last_price = dataset_to_use['Close'].iloc[-1]
        support, resistance = self.calculate_support_resistance(last_price)
        dataset_to_use['support'] = [self.calculate_support_resistance(dataset_to_use['Close'].iloc[i])[0] for i in
                                     range(len(dataset_to_use))]
        dataset_to_use['resistance'] = [self.calculate_support_resistance(dataset_to_use['Close'].iloc[i])[1] for i in
                                        range(len(dataset_to_use))]

        # consecutive_below_resistance = 0
        # consecutive_above_support = 0
        # max_consecutive_below_resistance = 0
        # max_consecutive_above_support = 0
        # touch_resistance_count = 0
        # touch_support_count = 0
        # Aggiunta delle colonne is_interesting e signal
        dataset_to_use['is_interesting'] = 0
        dataset_to_use['signal'] = 0

        # for index in range(0, period):  # Adjust loop range
        #     open_price = dataset_to_use['Open'].iloc[-period + index]
        #     high_price = dataset_to_use['High'].iloc[-period + index]
        #     low_price = dataset_to_use['Low'].iloc[-period + index]
        #     close_price = dataset_to_use['Close'].iloc[-period + index]
        #
        #     # Check for consecutive resistance interactions
        #     if resistance is not None and close_price <= resistance and open_price <= resistance:
        #         consecutive_below_resistance += 1
        #     else:
        #         max_consecutive_below_resistance = max(max_consecutive_below_resistance, consecutive_below_resistance)
        #         consecutive_below_resistance = 0
        #
        #     # Check for consecutive support interactions
        #     if support is not None and close_price >= support and open_price >= support:
        #         consecutive_above_support += 1
        #     else:
        #         max_consecutive_above_support = max(max_consecutive_above_support, consecutive_above_support)
        #         consecutive_above_support = 0
        #
        #     # Check for resistance and support touches
        #     if high_price >= resistance * 0.98 and high_price <= resistance:
        #         touch_resistance_count += 1
        #     if low_price <= support * 1.02 and low_price >= support:
        #         touch_support_count += 1

        # interesting_below_resistance = max_consecutive_below_resistance >= period - 3
        # interesting_above_support = max_consecutive_above_support >= period - 3

        # Analisi della resistenza e del supporto
        for i in range(len(dataset_to_use) - period, len(dataset_to_use)):
            # current_close = dataset_to_use['Close'].iloc[i]
            current_support = dataset_to_use['support'].iloc[i]
            current_resistance = dataset_to_use['resistance'].iloc[i]

            df_segment = dataset_to_use.iloc[i:i+period]
            support_broken, resistance_broken = self.check_support_resistance_break(
                                        df=df_segment,
                                        period=period,
                                        current_support=current_support,
                                        current_resistance=current_resistance
                                    )



            support_approach_count_gap = self.check_hloc_proximity_with_gap(df=df_segment,
                                                                reference_value=current_support, role='support')
            resistance_approach_count_gap = self.check_hloc_proximity_with_gap(df=df_segment,
                                                                reference_value=current_resistance, role='resistance')
            support_approach_count_approx = self.check_hloc_proximity(df=df_segment,
                                                                reference_value=current_support, role='support')
            resistance_approach_count_approx = self.check_hloc_proximity(df=df_segment,
                                                                reference_value=current_resistance, role='resistance')

            # Impostazione della colonna is_interesting
            if (not support_broken and not resistance_broken
                    and (support_approach_count_gap or support_approach_count_approx) and
                    (resistance_approach_count_gap or resistance_approach_count_approx)) :
                dataset_to_use['is_interesting'].iloc[i] = 3
            elif not support_broken and (support_approach_count_gap or support_approach_count_approx):
                dataset_to_use['is_interesting'].iloc[i] = 1
            elif not resistance_broken and (resistance_approach_count_gap or resistance_approach_count_approx):
                dataset_to_use['is_interesting'].iloc[i] = 2
            else:
                dataset_to_use['is_interesting'].iloc[i] = 0

        # Calcolo del signal in base alle ultime condizioni di is_interesting
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

        if dataset_to_use['is_interesting'].iloc[-1] == 1:
            previous_support = dataset_to_use['support'].iloc[-1]
            image = self.image.create_chart_with_horizontal_lines(lines=[support], max_points=period+10)
            result = {
                "status": "below_resistance",
                "details": {
                    "support": previous_support,
                    "enter_price": previous_support - 0.10,
                    "stop_loss": previous_support + 0.20,
                    "take_profit": previous_support - 0.50
                }
            }
        elif dataset_to_use['is_interesting'].iloc[-1] == 2:
            previous_resistance = dataset_to_use['resistance'].iloc[-1]
            image = self.image.create_chart_with_horizontal_lines(lines=[resistance], max_points=period+10)
            result = {
                "status": "above_support",
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
            image = self.image.create_chart_with_more_horizontal_lines(lines=[support, resistance],
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

        return result, image, dataset_to_use

    def clear_img_temp_files(self):
        self.image.clear_temp_files()

    def check_support_resistance_break(self, df, period, current_support, current_resistance):
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
        support_broken = False
        resistance_broken = False

        # Assicurati che df abbia un numero sufficiente di righe
        if len(df) < period:
            raise ValueError("Il DataFrame non contiene un numero sufficiente di righe per il periodo specificato.")

        # Itera attraverso il periodo specificato
        for i in range(len(df)):
            if df['Close'].iloc[i] > current_resistance or df['Open'].iloc[i] > current_resistance:
                resistance_broken = True
            if df['Close'].iloc[i] < current_support or df['Open'].iloc[i] < current_support:
                support_broken = True

            if support_broken or resistance_broken:
                break

        return support_broken, resistance_broken

    def check_hloc_proximity(self, df, reference_value, role, approximation=0.02):
        """
        Verifica se almeno uno dei valori HLOC si avvicina al valore di riferimento
        (considerato come resistenza o supporto) con un'approssimazione del 2% per
        almeno tre volte consecutive.

        Args:
        df (pd.DataFrame): DataFrame contenente le colonne HLOC.
        reference_value (float): Valore di riferimento per il confronto.
        role (str): 'resistance' o 'support', a seconda del ruolo del valore di riferimento.
        approximation (float): Percentuale di approssimazione (default 2%).

        Returns:
        bool: True se la condizione è soddisfatta, altrimenti False.
        """
        # Calcola il limite inferiore e superiore
        lower_bound = reference_value * (1 - approximation)
        upper_bound = reference_value * (1 + approximation)

        # Conta le occorrenze consecutive
        consecutive_count = 0

        for index, row in df.iterrows():
            if role == 'resistance' and row['High'] >= upper_bound:
                # Verifica per la resistenza
                consecutive_count += 1
                if consecutive_count >= 3:
                    return True
            elif role == 'support' and row['Low'] <= lower_bound:
                # Verifica per il supporto
                consecutive_count += 1
                if consecutive_count >= 3:
                    return True
            else:
                consecutive_count = 0

        return False

    def check_hloc_proximity_with_gap(self, df, reference_value, role, approximation=0.02, min_gap=3):
        """
        Verifica se un valore HLOC si avvicina al valore predefinito (considerato come resistenza o supporto)
        almeno due volte, con almeno tre righe di differenza tra queste due occorrenze.

        Args:
        df (pd.DataFrame): DataFrame contenente le colonne HLOC.
        reference_value (float): Valore di riferimento per il confronto.
        role (str): 'resistance' o 'support', a seconda del ruolo del valore di riferimento.
        approximation (float): Percentuale di approssimazione (default 2%).
        min_gap (int): Numero minimo di righe di differenza tra le occorrenze.

        Returns:
        bool: True se la condizione è soddisfatta, altrimenti False.
        """
        # Calcola il limite inferiore e superiore
        lower_bound = reference_value * (1 - approximation)
        upper_bound = reference_value * (1 + approximation)

        # Indice dell'ultima occorrenza in termini di posizione
        last_occurrence_pos = None

        for index, row in df.iterrows():
            current_pos = df.index.get_loc(index)

            if role == 'resistance' and row['High'] >= upper_bound:
                # Verifica per la resistenza
                if last_occurrence_pos is not None and (current_pos - last_occurrence_pos) >= min_gap:
                    return True
                last_occurrence_pos = current_pos
            elif role == 'support' and row['Low'] <= lower_bound:
                # Verifica per il supporto
                if last_occurrence_pos is not None and (current_pos - last_occurrence_pos) >= min_gap:
                    return True
                last_occurrence_pos = current_pos

        return False



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
