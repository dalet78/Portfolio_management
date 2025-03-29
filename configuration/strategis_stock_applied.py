from datetime import time

# Dizionario con le strategie e le liste di stock corrispondenti
strategies_stock_applied = {
    "EMA_Cross_ema50": {
        "tickers": ["CFG", "CZR", "GEN", "PARA", "PPL", "TFC", "WBD"],
        "check_function": "check_ema_cross_ema50",
        "start_time":time(15, 35),
        "stop_time":time(15, 50)
    },
    "EMA_Cross_candle": {
        "tickers": ["BAX", "CTRA", "EXC", "FITB", "FXC", "KMI", "UDR", "WBA"],
        "check_function": "check_ema_cross_candle",
        "start_time":time(15, 35),
        "stop_time":time(15, 50)
    },

    "SMA_Cross_sma50": {
        "tickers": [ "FITB", "HPQ", "IPG", "LVS", "NCLH", "NWSA"],
        "check_function": "check_sma_cross_sma50",
        "start_time":time(15, 35),
        "stop_time":time(15, 50)
    },
    "SMA_Cross_candle": {
        "tickers": ["DVN", "LUV", "NI", "WBD"],
        "check_function": "check_sma_cross_candle",
        "start_time":time(15, 35),
        "stop_time":time(15, 50)
    },
    # "EMA_Cross_cents": {
    #     "tickers": ["UDR"],
    #     "check_function": "check_ema_cross_cents"
    # },
    # "SMA_Cross_cents": {
    #     "tickers": ["BAX"],
    #     "check_function": "check_sma_cross_cents"
    # },
    # "SMA_Cross_combined": {
    #     "tickers": ["LVS"],
    #     "check_function": "check_sma_cross_combined"
    # },
    "VWAP_diff_signal": {
        "tickers": ["MGM", "MTCH", "CZR", "WBA", "WBD","CMCSA", "FITB", "IPG", "MOS", "GEN", "WY", "PCG", "DOC"],
        "check_function": "check_vwap_diff_signal",
        "start_time":time(16, 30),
        "stop_time":time(18, 0)
    }
}

# Funzione per ottenere la lista di stock data una strategia
def get_stock_list(strategy_name):
    return strategies_stock_applied.get(strategy_name, [])

def get_all_check_functions():
    """Restituisce una lista di tutte le check_function definite nelle strategie."""
    return list({
        strategy_data["check_function"]
        for strategy_data in strategies_stock_applied.values()
        if "check_function" in strategy_data
    })

# Esempio di utilizzo
selected_stocks = get_stock_list("SMA_Cross")

