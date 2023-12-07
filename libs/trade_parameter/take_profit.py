def calculate_take_profit(entry_price, take_profit_type, percentage=None, atr_value=None, fixed_value=None, resistance_level=None):
    """
    Calcola il valore di take profit in base al metodo scelto.

    Args:
    entry_price (float): Prezzo di entrata.
    take_profit_type (str): Tipo di take profit ('percentuale', 'atr', 'fisso', 'resistenza').
    percentage (float, optional): Percentuale per il take profit percentuale.
    atr_value (float, optional): Valore ATR per il take profit ATR.
    fixed_value (float, optional): Valore fisso per il take profit fisso.
    resistance_level (float, optional): Livello di resistenza per il take profit basato su resistenza.

    Returns:
    float: Valore di take profit.
    """
    if take_profit_type == 'percentuale':
        if percentage is None:
            raise ValueError("È necessario fornire una percentuale per il take profit percentuale.")
        return entry_price * (1 + percentage / 100)

    elif take_profit_type == 'atr':
        if atr_value is None:
            raise ValueError("È necessario fornire un valore ATR per il take profit ATR.")
        return entry_price + atr_value

    elif take_profit_type == 'fisso':
        if fixed_value is None:
            raise ValueError("È necessario fornire un valore fisso per il take profit fisso.")
        return entry_price + fixed_value

    elif take_profit_type == 'resistenza':
        if resistance_level is None:
            raise ValueError("È necessario fornire un livello di resistenza per il take profit basato su resistenza.")
        return resistance_level

    else:
        raise ValueError("Tipo di take profit non riconosciuto.")

# Esempio di utilizzo della funzione
entry_price = 100
take_profit = calculate_take_profit(entry_price, 'percentuale', percentage=10)
print("Take Profit:", take_profit)
