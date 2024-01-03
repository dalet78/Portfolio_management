from datetime import datetime, timedelta
import pandas as pd
from VMP_association import calculate_market_profile_values, load_data

def split_data_by_day(df, start_date, end_date):
    """Divide i dati in DataFrame separati per ogni giorno della settimana precedente."""
    dfs_per_day = []
    daily_groups = df.groupby(pd.Grouper(freq='D'))
    for date, group in daily_groups:
        if not group.empty and start_date <= date <= end_date:
            day_df = group.copy()
            dfs_per_day.append(day_df)
    return dfs_per_day

def calculate_total_volume(dfs_per_day):
    """Calcola il volume totale per la settimana precedente."""
    total_volume = 0
    for day_df in dfs_per_day:
        total_volume += day_df['Volume'].sum()
    return total_volume

# Ottieni la data corrente
today = datetime.now()

# Calcola l'inizio della settimana corrente (lunedì)
start_of_current_week = today - timedelta(days=today.weekday())

# Calcola l'inizio e la fine della settimana precedente
end_of_last_week = start_of_current_week - timedelta(days=1)
start_of_last_week = end_of_last_week - timedelta(days=4)

# Percorso del file di dati
source_directory = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management"
data_filepath = f"{source_directory}/Data/SP500/5min/AAL_historical_data.csv"
# Carica i dati
df = load_data(data_filepath)

# Dividi i dati per giorno per la settimana precedente
dfs_per_day = split_data_by_day(df, start_of_last_week, end_of_last_week)

# Calcola i valori di market profile per ogni giorno della settimana precedente
market_profile_values = calculate_market_profile_values(dfs_per_day)

# Calcola il volume totale per la settimana precedente
total_volume = calculate_total_volume(dfs_per_day)

print("Volume totale per la settimana precedente:", total_volume)