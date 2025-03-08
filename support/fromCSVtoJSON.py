import csv
import json
import os

# Percorsi dei file
csv_file_path = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Data/list_companies.csv"
json_file_path = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/json_files/list_companies.json"

# Verifica se il file CSV esiste
if not os.path.exists(csv_file_path):
    print(f"Errore: Il file CSV '{csv_file_path}' non esiste.")
    exit(1)

data = {}

# Lettura del CSV e conversione in JSON
try:
    with open(csv_file_path, mode="r", encoding="utf-8-sig") as file:
        csv_reader = csv.DictReader(file, delimiter=',')

        # Pulizia dei nomi delle colonne per evitare problemi con spazi
        csv_reader.fieldnames = [name.strip() for name in csv_reader.fieldnames]

        for row in csv_reader:
            symbol = row.get("Symbol", "").strip()
            company_name = row.get("Company Name", "").strip()  # CORRETTO IL NOME DELLA COLONNA

            if symbol and company_name:  # Evita righe vuote o errate
                data[symbol] = company_name

    # Scrittura su JSON
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)

    print(f"✅ File JSON creato con successo: {json_file_path}")

except Exception as e:
    print(f"❌ Errore durante la conversione: {e}")
