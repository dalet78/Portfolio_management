import json
import requests
import pandas as pd
from datetime import datetime
from libs.logger import MyLogger

class WorldBankDataDownloader:
    """
    # Uso della classe
    from MacroEconomic.import_me_data import WorldBankDataDownloader as wbd
    
    config_file = 'path_to_your_config_file.json'  # Update with the correct path
    downloader = WorldBankDataDownloader(config_file)
    downloader.save_data_to_csv()
    downloader.update_config()
    """
    def __init__(self, config_dict):
        self.logger = MyLogger
        self.config = config_dict
        
        self.base_url = self.config['api_base_url']
        self.api_key = self.config['api_key']
        self.countries = self.config['countries']
        self.indicator_descriptions = self.config.get('indicator_description', {})

    def fetch_data(self, country_code, indicator_code, start_year):
        self.logger.info(f'Connessione al sito e scarico i dati: {country_code}, {indicator_code}\n')
        url = f"{self.base_url}country/{country_code}/indicator/{indicator_code}?format=json&date={start_year}:2020&api_key={self.api_key}"
        response = requests.get(url)
        self.logger.info(f'Dati scaricati: {country_code}, {indicator_code}\n')
        return response.json()

    def save_country_data_to_csv(self, country, indicators):
        indicators = country_data['indicators']
        last_update = country_data.get('last_update', '2000')
    
        self.logger.info(f'Converto i dati in CSV: {country_code}, {indicator_code}\n')
        all_data = []
        for indicator_name, indicator_code in indicators.items():
            data = self.fetch_data(country, indicator_code, last_update)
            if data and len(data) > 1 and 'indicator' in data[1][0]:
                for record in data[1]:
                    all_data.append({
                        'Date': record['date'],
                        'Indicator': indicator_name,
                        'Value': record['value'],
                        'Description': ' '.join(self.indicator_descriptions.get(indicator_name, []))
                    })

        df = pd.DataFrame(all_data)
        df.to_csv(f'world_bank_data_{country}.csv', index=False)

    def save_data_to_csv(self):
        for country, indicators in self.countries.items():
            self.save_country_data_to_csv(country, indicators['indicators'])

    def update_config(self):
        current_year = datetime.now().year
        for country in self.countries:
            self.countries[country]['last_update'] = str(current_year)
        # self.config['last_update'] = str(current_year)
        # with open(self.config_file, 'w') as file:
        #     json.dump(self.config, file, indent=4)
