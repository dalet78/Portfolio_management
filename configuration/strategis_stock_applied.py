# Dizionario con le strategie e le liste di stock corrispondenti
strategies_stock_applied = {
    "SMA_Cross_sma50": ["FITB","HPQ","IPG","MTCH","NCLH","NWSA"],
    "EMA_Cross_ema50": ["CFG","CZR","GEN","PARA","PPL","TFC", "WBA"],
    "EMA_Cross_candle": ["CTRA","EXC", "FXC","KMI"],
    "EMA_Cross_cents": ["AMCR","UDR"],
    "SMA_Cross_candle": ["DVN", "NI", "WBD"],
    "SMA_Cross_cents": ["BAX"],
    "SMA_Cross_combined": ["LVS"]
}

# Funzione per ottenere la lista di stock data una strategia
def get_stock_list(strategy_name):
    return strategies_stock_applied.get(strategy_name, [])

# Esempio di utilizzo
selected_stocks = get_stock_list("SMA_Cross")
print(f"Stock selezionati per SMA_Cross: {selected_stocks}")
