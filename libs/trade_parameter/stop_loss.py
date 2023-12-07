import numpy as np


def calculate_stop_loss(entry_price, stop_loss_type, percentage=None, atr_value=None, fixed_value=None, support_level=None):
    """
    Calcola il valore di stop loss in base al metodo scelto.

    Args:
    entry_price (float): Prezzo di entrata.
    stop_loss_type (str): Tipo di stop loss ('percentuale', 'atr', 'fisso', 'supporto').
    percentage (float, optional): Percentuale per lo stop loss percentuale.
    atr_value (float, optional): Valore ATR per lo stop loss ATR.
    fixed_value (float, optional): Valore fisso per lo stop loss fisso.
    support_level (float, optional): Livello di supporto per lo stop loss basato su supporto.

    Returns:
    float: Valore di stop loss.
    """
    if stop_loss_type == 'percentuale':
        if percentage is None:
            raise ValueError("È necessario fornire una percentuale per lo stop loss percentuale.")
        return entry_price * (1 - percentage / 100)

    elif stop_loss_type == 'atr':
        if atr_value is None:
            raise ValueError("È necessario fornire un valore ATR per lo stop loss ATR.")
        return entry_price - atr_value

    elif stop_loss_type == 'fisso':
        if fixed_value is None:
            raise ValueError("È necessario fornire un valore fisso per lo stop loss fisso.")
        return entry_price - fixed_value

    elif stop_loss_type == 'supporto':
        if support_level is None:
            raise ValueError("È necessario fornire un livello di supporto per lo stop loss basato su supporto.")
        return support_level

    else:
        raise ValueError("Tipo di stop loss non riconosciuto.")

# Esempio di utilizzo della funzione
entry_price = 100
stop_loss = calculate_stop_loss(entry_price, 'percentuale', percentage=5)
print("Stop Loss:", stop_loss)