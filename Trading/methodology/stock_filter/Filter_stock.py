import pandas as pd


def scan_stocks(stock_data, min_price, max_price, min_volume, max_volume):
    """
    Filtra le azioni in base al prezzo e al volume medio.

    :param stock_data: DataFrame contenente i dati delle azioni.
    :param min_price: Prezzo minimo per il filtro.
    :param max_price: Prezzo massimo per il filtro.
    :param min_volume: Volume medio minimo per il filtro.
    :param max_volume: Volume medio massimo per il filtro.
    :return: DataFrame delle azioni filtrate.
    """
    # Filtra in base al prezzo
    filtered_data = stock_data[(stock_data['Price'] >= min_price) & (stock_data['Price'] <= max_price)]

    # Filtra in base al volume medio
    filtered_data = filtered_data[
        (filtered_data['AverageVolume'] >= min_volume) & (filtered_data['AverageVolume'] <= max_volume)]

    return filtered_data

# Esempio di utilizzo
# Supponiamo che stock_data sia un DataFrame con colonne 'Price' e 'AverageVolume'
# stock_data = pd.read_csv('path_to_your_stock_data.csv')

# Filtra le azioni
# filtered_stocks = scan_stocks(stock_data, min_price=XX, max_price=YY, min_volume=1e6, max_volume=10e6)
