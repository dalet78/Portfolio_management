# Mappatura tra intervallo e strategie
INTERVAL_STRATEGIES = {
    #primo valore cartella.nome_file, secondo valore funzione nel file
    # "5m": [("Trading.strategies_BT.sma_strategy_start_session", "sma_cross_trading"),
    #        ("Trading.strategies_BT.vwap_diff_strategy", "vwap_diff_trading"),
    #        ("Trading.strategies_BT.ema_strategy_start_session", "ema_cross_trading"),
    #        ("Trading.strategies_BT.breakout_sma_strategy", "orb_sma_trading"),
    #        ("Trading.strategies_BT.vwap_reversal_with_rsi_strategy", "vwap_rsi_reversal_trading")
    #################################################
        "5m": [("Trading.strategies_BT.sma_strategy_start_session", "sma_cross_trading"),
                ("Trading.strategies_BT.ema_strategy_start_session", "ema_cross_trading")
    #################################################
           ],
    "daily": [],
    "weekly": []
}
INTERVAL_OPPORTUNITES = {
    "5m": [],
    "daily": [("Trading.opportunity_BT.blocked_stock", "blocked_stock")],
    "weekly": []
}