from fredapi import Fred
import pandas as pd

et_series(series_id)
            return data
        except Exception as e:
            print(f"Error fetching data for {series_id}: {e}")
            return pd.Series()

    def save_data_to_csv(self, country):
        start_date = self.config_dict["countries"][f"{country}"]["start_date"]
        series_dict= self.config_dict["countries"][f"{country}"]["indicators"]
        for series_name, series_id in series_dict.items():
            data = self.fetch_series_data(series_id)
            if not data.empty:
                if start_date:
                    data = data[data.index >= start_date]class FredDataDownloader:
    """
    # Uso della classe
    api_key = 'YOUR_FRED_API_KEY'
    series_dict = {
        'GDP': 'GDP',  # Usa gli ID serie appropriati
        # Aggiungi altre serie qui
    }

    downloader = FredDataDownloader(api_key)
    downloader.save_data_to_csv(series_dict, start_date='2000-01-01')
    """
    def __init__(self, api_key, config_dict):
        self.fred = Fred(api_key)
        self.me_path = "portfolio_management/macro_economic/Data"
        self.config_dict = config_dict
        

    def fetch_series_data(self, series_id):
        try:
            data = self.fred.g
                data.to_csv(f"{self.me_path}/{country}/{series_name}.csv")


