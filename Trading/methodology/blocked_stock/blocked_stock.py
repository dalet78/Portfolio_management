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

        consecutive_below_resistance = 0
        consecutive_above_support = 0
        max_consecutive_below_resistance = 0
        max_consecutive_above_support = 0
        touch_resistance_count = 0
        touch_support_count = 0
        # Aggiunta delle colonne is_interesting e signal
        dataset_to_use['is_interesting'] = 0
        dataset_to_use['signal'] = 0

        for index in range(0, period):  # Adjust loop range
            open_price = dataset_to_use['Open'].iloc[-period + index]
            high_price = dataset_to_use['High'].iloc[-period + index]
            low_price = dataset_to_use['Low'].iloc[-period + index]
            close_price = dataset_to_use['Close'].iloc[-period + index]

            # Check for consecutive resistance interactions
            if resistance is not None and close_price <= resistance and open_price <= resistance:
                consecutive_below_resistance += 1
            else:
                max_consecutive_below_resistance = max(max_consecutive_below_resistance, consecutive_below_resistance)
                consecutive_below_resistance = 0

            # Check for consecutive support interactions
            if support is not None and close_price >= support and open_price >= support:
                consecutive_above_support += 1
            else:
                max_consecutive_above_support = max(max_consecutive_above_support, consecutive_above_support)
                consecutive_above_support = 0

            # Check for resistance and support touches
            if high_price >= resistance * 0.98 and high_price <= resistance:
                touch_resistance_count += 1
            if low_price <= support * 1.02 and low_price >= support:
                touch_support_count += 1

        interesting_below_resistance = max_consecutive_below_resistance >= period - 3
        interesting_above_support = max_consecutive_above_support >= period - 3

        # Analisi della resistenza e del supporto
        for i in range(len(dataset_to_use) - period, len(dataset_to_use)):
            current_support = dataset_to_use['support'].iloc[i]
            current_resistance = dataset_to_use['resistance'].iloc[i]

            # Inizializza le variabili per verificare la condizione
            within_support_range = True
            within_resistance_range = True

            for j in range(i, i + period):
                if j < len(dataset_to_use):
                    # Controlla se i prezzi sono entro un range di 2 dollari sopra il supporto
                    if not (current_support <= dataset_to_use['High'].iloc[j] <= current_support + 2 and
                            current_support <= dataset_to_use['Low'].iloc[j] <= current_support + 2 and
                            current_support <= dataset_to_use['Open'].iloc[j] <= current_support + 2 and
                            current_support <= dataset_to_use['Close'].iloc[j] <= current_support + 2):
                        within_support_range = False

                    # Controlla se i prezzi sono entro un range di 2 dollari sotto la resistenza
                    if not (current_resistance - 2 <= dataset_to_use['High'].iloc[j] <= current_resistance and
                            current_resistance - 2 <= dataset_to_use['Low'].iloc[j] <= current_resistance and
                            current_resistance - 2 <= dataset_to_use['Open'].iloc[j] <= current_resistance and
                            current_resistance - 2 <= dataset_to_use['Close'].iloc[j] <= current_resistance):
                        within_resistance_range = False

            # Impostazione della colonna is_interesting
            if within_support_range and within_resistance_range:
                dataset_to_use['is_interesting'].iloc[i] = 3
            elif within_support_range:
                dataset_to_use['is_interesting'].iloc[i] = 1
            elif within_resistance_range:
                dataset_to_use['is_interesting'].iloc[i] = 2
            else:
                dataset_to_use['is_interesting'].iloc[i] = 0

        # Calcolo del signal in base alle ultime condizioni di is_interesting
        for i in range(len(dataset_to_use)):
            last_is_interesting = dataset_to_use['is_interesting'].iloc[i -1]
            previous_support = dataset_to_use['support'].iloc[ - 1]
            previous_resistance = dataset_to_use['resistance'].iloc[i - 1]

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
            elif current_is_interesting == 3:
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
            image = self.image.create_chart_with_horizontal_lines(lines=[dataset_to_use['resistance'].iloc[-1]], max_points=period)
            result = {
                "status": interesting_below_resistance,
                "details": {
                    "resistence": dataset_to_use['resistance'].iloc[-1],
                    "enter_price": resistance + 0.10,
                    "stop_loss": resistance - 0.20,
                    "take_profit": resistance + 0.50,
                }
            }
        elif dataset_to_use['is_interesting'].iloc[-1] == 2:
            image = self.image.create_chart_with_horizontal_lines(lines=[dataset_to_use['support'].iloc[-1]], max_points=period)
            result = {
                "status": interesting_above_support,
                "details": {
                    "support": dataset_to_use['support'].iloc[-1],
                    "enter_price": support - 0.10,
                    "stop_loss": support + 0.20,
                    "take_profit": support - 0.50,
                }
            }
        else:
            result = None
            image = None

        return result, image, dataset_to_use

    def clear_img_temp_files(self):
        self.image.clear_temp_files()


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
                enhanced_strategy = TradingAnalyzer(data)
                result, image, new_data = enhanced_strategy.check_signal(period=20)
                filtred_interesting_dataset =new_data[new_data['is_interesting'] != 0]
                count_interesting = filtred_interesting_dataset['is_interesting'].count()
                filtred_signal_dataset = new_data[new_data['signal'] != 0]
                count_signal = filtred_signal_dataset['signal'].count()
                if result:
                    report.add_content(f'stock = {item} \n')
                    report.add_commented_image(df=data, comment=f'Description = {result["details"]}', image_path=image)
                if not filtred_interesting_dataset.empty:
                    report.add_content(f'stock = {item} \n count interesting= {count_interesting}\n')
                    report.add_content(f'stock = {item} \n count signal= {count_signal}\n')


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
