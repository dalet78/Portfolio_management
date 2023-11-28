import pandas as pd
import matplotlib.pyplot as plt
import os

class EconomicDataGrapher:
    """
    from libs.economic_graph_designer.py import EconomicDataGrapher as egd
    
    csv_folder_path = 'path_to_your_csv_files_folder'  # Update with the correct path
    grapher = EconomicDataGrapher(csv_folder_path)
    grapher.generate_graphs()
        """
    def __init__(self, csv_folder_path):
        self.csv_folder_path = csv_folder_path

    def read_csv_data(self, file_path):
        return pd.read_csv(file_path)

    def plot_data(self, df, country, indicator):
        plt.figure(figsize=(10, 6))
        plt.plot(df['Date'], df['Value'], marker='o')
        plt.title(f'{indicator} over Time in {country}')
        plt.xlabel('Year')
        plt.ylabel(indicator)
        plt.grid(True)
        plt.savefig(f"{self.csv_folder_path}/{country}_{indicator}_graph.png")
        plt.close()

    def generate_graphs(self):
        for file in os.listdir(self.csv_folder_path):
            if file.endswith('.csv'):
                country = file.split('_')[3].split('.')[0]  # Assumes the file name format is 'world_bank_data_[country].csv'
                df = self.read_csv_data(os.path.join(self.csv_folder_path, file))
                indicators = df['Indicator'].unique()
                for indicator in indicators:
                    df_indicator = df[df['Indicator'] == indicator]
                    self.plot_data(df_indicator, country, indicator)