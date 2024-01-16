import os
from datetime import datetime


source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
def crea_cartella_con_data(weekly=False):
    # Ottieni la data odierna
    data_odierna = datetime.now().strftime("%Y-%m-%d")

    # Crea il percorso della cartella con la data odierna
    if not weekly:
        percorso_cartella = os.path.join(f"{source_directory}/Reports", data_odierna)
    else:
        percorso_cartella = os.path.join(f"{source_directory}/Reports", f"weekly-{data_odierna}")

    # Verifica se la cartella esiste già, altrimenti creala
    if not os.path.exists(percorso_cartella):
        os.makedirs(percorso_cartella)
        print(f"Cartella creata: {percorso_cartella}")
    else:
        print(f"La cartella esiste già: {percorso_cartella}")

    return percorso_cartella

def sposta_file_in_cartella(file_da_spostare, cartella_destinazione):
    # Verifica se il file da spostare esiste
    if os.path.exists(file_da_spostare):
        # Ottieni il percorso completo del file
        percorso_file = os.path.join(os.getcwd(), file_da_spostare)

        # Sposta il file nella cartella di destinazione
        nuovo_percorso_file = os.path.join(cartella_destinazione, os.path.basename(file_da_spostare))
        os.rename(percorso_file, nuovo_percorso_file)

        print(f"File spostato con successo in: {nuovo_percorso_file}")
    else:
        print(f"File non trovato: {file_da_spostare}")