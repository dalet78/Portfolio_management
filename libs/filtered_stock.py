import json
import pandas as pd

source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
def return_filtred_list(index="SP500", price_range= (10,50), volume_range=(500,100000000)):
    """
      Legge i ticker dagli stock SP500 e Russell2000, li combina e filtra in base al prezzo e al volume.

      Returns:
      lista of stock
    """
    if index == "SP500":
        with open(f"{source_directory}/json_files/SP500-stock.json", 'r') as file:
            tickers = json.load(file)
    elif index == "Russel":
        with open(f"{source_directory}/json_files/russell2000.json", 'r') as file:
            tickers = json.load(file)
    elif index == "Nasdaq":
        with open(f"{source_directory}/json_files/nasdaq.json", 'r') as file:
            tickers = json.load(file)
    else:
        raise ValueError("Index non valido. Scegliere tra 'SP500' e 'Russel'.")

    tickers_list = list(tickers.keys())
    filtered_stocks = filtred_stock(index, tickers_list, price_range, volume_range)

    return filtered_stocks

def filtred_stock(index, tickers_list, price_range, volume_range):
    filtered_stock_list = []
    for item in tickers_list:
        try:
            data = pd.read_csv(f"{source_directory}/Data/{index}/Daily/{item}_historical_data.csv")
            # Calcola il volume medio
            average_volume = data['Volume'].mean()

            # Filtra in base al range di prezzo e al volume medio
            if (data['Close'].iloc[-1] >= price_range[0]) and (data['Close'].iloc[-1] <= price_range[1]) and \
                    (average_volume >= volume_range[0]) and (average_volume <= volume_range[1]):
                filtered_stock_list.append(item)

        except FileNotFoundError:
            print(f"Dati non trovati per {item}")
        except Exception as e:
            print(f"Errore durante l'elaborazione di {item}: {e}")

    return filtered_stock_list


