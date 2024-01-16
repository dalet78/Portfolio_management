import pandas as pd
from market_profile import MarketProfile

def load_data(filepath):
    """Carica i dati dal file CSV."""
    df = pd.read_csv(filepath, parse_dates=['Datetime'])
    df.rename(columns={'Datetime': 'datetime'}, inplace=True)
    df.set_index('datetime', inplace=True)
    return df

def split_data_by_day(df):
    """Divide i dati in DataFrame separati per ogni giorno."""
    dfs_per_day = []
    daily_groups = df.groupby(pd.Grouper(freq='D'))
    for date, group in daily_groups:
        if not group.empty:
            day_df = group.copy()
            dfs_per_day.append(day_df)
    return dfs_per_day

def calculate_market_profile_values(dfs_per_day):
    """Calcola i valori di market profile per ogni giorno."""
    values_per_day = []
    for day_df in dfs_per_day:
        mp = MarketProfile(day_df)
        mp_slice = mp[day_df.index.min():day_df.index.max()]
        # mp_slice.make()
        vah = mp_slice.value_area[1]
        poc = mp_slice.poc_price
        val = mp_slice.value_area[0]
        values_per_day.append({
            'Date': day_df.index.min().date(),
            'VAL': val,
            'POC': poc,
            'VAH': vah
        })
    return values_per_day

def calculate_overlap_percent(range1, range2):
    """Calcola la sovrapposizione percentuale tra due intervalli."""
    max_start = max(range1[0], range2[0])
    min_end = min(range1[1], range2[1])
    overlap = max(0, min_end - max_start)
    total_range = min(range1[1], range2[1]) - max(range1[0], range2[0])
    return (overlap / total_range) * 100 if total_range else 0


def check_value_area_overlap(values, first_index, second_index, overlap_threshold):
    """
    Controlla se le value area di due giorni specificati si sovrappongono per almeno una percentuale definita.

    :param values: Lista dei valori di market profile per ogni giorno.
    :param first_index: Indice del primo giorno nel confronto.
    :param second_index: Indice del secondo giorno nel confronto.
    :param overlap_threshold: Soglia percentuale per considerare una sovrapposizione significativa.
    :return: True se la sovrapposizione è almeno della soglia specificata, altrimenti False.
    """
    # Assicurati che gli indici siano validi e che ci siano abbastanza dati
    if first_index < len(values) and second_index < len(values) and first_index != second_index:
        # Ottieni le value area dei giorni specificati
        first_day = values[first_index]
        second_day = values[second_index]

        # Calcola la sovrapposizione percentuale
        overlap_percent = calculate_overlap_percent(
            (first_day['VAL'], first_day['VAH']),
            (second_day['VAL'], second_day['VAH'])
        )

        # Controlla se la sovrapposizione è almeno della soglia specificata
        return overlap_percent >= overlap_threshold

    return False  # Restituisce False se gli indici non sono validi o non ci sono abbastanza dati


def merge_specific_dfs_if_overlap(dfs, values, first_index, second_index, overlap_threshold):
    """
       Unisce due DataFrame specificati se la loro sovrapposizione è maggiore della soglia.

       :param dfs: Lista dei DataFrame divisi per giorno.
       :param values: Lista dei valori di market profile per ogni giorno (VAL, POC, VAH).
       :param first_index: Indice del primo giorno nel confronto.
       :param second_index: Indice del secondo giorno nel confronto.
       :param overlap_threshold: Soglia percentuale per considerare una sovrapposizione significativa.
       :return: Lista aggiornata dei DataFrame.
       """
    # Assicurati che gli indici siano validi e che ci siano abbastanza dati
    if first_index < len(dfs) and second_index < len(dfs) and first_index != second_index:
        # Controlla la sovrapposizione usando gli indici e la soglia forniti
        is_overlapping = check_value_area_overlap(values, first_index, second_index, overlap_threshold)

        if is_overlapping:
            # Unisci i due DataFrame specificati
            merged_df = pd.concat([dfs[first_index], dfs[second_index]])

            # Crea una nuova lista escludendo i DataFrame uniti e includendo quello unito
            new_dfs = [df for i, df in enumerate(dfs) if i not in [first_index, second_index]]
            new_dfs.append(merged_df)

            return new_dfs

    # Nessuna azione richiesta o indici non validi, restituisci l'originale
    return dfs

def reorder_dfs(dfs):
    """
    Riordina gli DataFrame in base al primo timestamp di ciascuno.

    :param dfs: Lista dei DataFrame da riordinare.
    :return: Lista dei DataFrame riordinati.
    """
    # Ottieni il primo timestamp di ciascun DataFrame e usa come chiave per l'ordinamento
    dfs.sort(key=lambda x: x.index.min())
    return dfs

def iterative_merge_dfs(dfs, overlap_threshold):
    """
    Continua a unire i DataFrame in 'dfs' finché c'è una sovrapposizione significativa tra i loro valori di market profile.

    :param dfs: Lista dei DataFrame divisi per giorno.
    :param overlap_threshold: Soglia percentuale per considerare una sovrapposizione significativa.
    :return: Lista aggiornata dei DataFrame e i loro corrispondenti valori di market profile.
    """
    values = calculate_market_profile_values(dfs)
    first_index_to_check = len(dfs) - 2
    second_index_to_check = len(dfs) - 1

    while first_index_to_check >= 0 and second_index_to_check > 0:
        original_length = len(dfs)

        # Controlla la sovrapposizione e unisci se necessario
        dfs = merge_specific_dfs_if_overlap(dfs, values, first_index_to_check, second_index_to_check, overlap_threshold)
        dfs = reorder_dfs(dfs)
        # Se il numero di DataFrame è cambiato, significa che c'è stata un'unione
        if len(dfs) < original_length:
            # Ricalcola i valori di market profile per tutti i DataFrame
            values = calculate_market_profile_values(dfs)
            # Aggiorna gli indici per il prossimo controllo
            second_index_to_check = len(dfs) - 1  # L'ultimo DataFrame ora è il risultato dell'unione
        else:
            # Se non c'è stata un'unione, passa al prossimo set di DataFrame
            second_index_to_check -= 1

        first_index_to_check = second_index_to_check - 1

    return dfs, values

def get_last_and_longest_dfs(dfs_per_day, overlap_threshold):
    # Iterative merge of DataFrames
    dfs_per_day_merged, merged_market_profile_values = iterative_merge_dfs(dfs_per_day, overlap_threshold)

    # Filtra i valori di market profile basandoti sulla lunghezza del DataFrame associato
    filtered_market_profiles = [
        (df, mp) for df, mp in zip(dfs_per_day_merged, merged_market_profile_values) if len(df) >= 234
    ]

    # Ordina la lista in base alla lunghezza dei DataFrame
    filtered_market_profiles.sort(key=lambda x: len(x[0]), reverse=True)

    # Restituisci solo gli ultimi due DataFrames
    if len(filtered_market_profiles) >= 2:
        last_df1, last_mp1 = filtered_market_profiles[-1]
        last_df2, last_mp2 = filtered_market_profiles[-2]
        return last_df1, last_mp1, last_df2, last_mp2
    elif len(filtered_market_profiles) == 1:
        last_df, last_mp = filtered_market_profiles[0]
        return last_df, last_mp, None, None
    else:
        return None, None, None, None
