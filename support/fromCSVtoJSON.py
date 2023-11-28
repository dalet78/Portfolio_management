import csv
import json

# Sostituisci 'path_to_your_csv.csv' con il percorso del tuo file CSV
csv_file_path = 'portfolio_management/json_files/SP500-stock.csv'
json_file_path = 'portfolio_management/json_files/SP500-stock.json'

data = {}
with open(csv_file_path, mode='r') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        symbol = row['Symbol']
        security = row['Security']
        data[symbol] = security

with open(json_file_path, 'w') as json_file:
    json.dump(data, json_file, indent=4)

print(f"File JSON creato: {json_file_path}")