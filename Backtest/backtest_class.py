class Backtester:
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.trades = []
        self.successful_trades = 0

    def run_backtest(self, result):
        position = result["details"]["position"]
        entry_price = result["details"]["entry_price"]
        stop_loss = result["details"]["stop_loss"]
        take_profit = result["details"]["take_profit"]
        trade_result, index = self.simulate_trade(self.historical_data, position, entry_price, stop_loss, take_profit)
        if trade_result == 'success':
            self.successful_trades += 1
            return index+1


    def simulate_trade(self, data, position, entry_price, stop_loss, take_profit):
        for index, row in data.iterrows():
            high, low = row['High'], row['Low']

            # Per una posizione di acquisto
            if position == 'buy':
                # Controlla se il prezzo raggiunge il take profit o lo stop loss
                if high >= take_profit:
                    return 'success',index
                elif low <= stop_loss:
                    return 'failure', index

            # Per una posizione di vendita
            elif position == 'sell':
                # Controlla se il prezzo raggiunge il take profit o lo stop loss
                if low <= take_profit:
                    return 'success', index
                elif high >= stop_loss:
                    return 'failure', index

    def get_results(self):
        total_trades = len(self.trades)
        success_rate = self.successful_trades / total_trades if total_trades > 0 else 0
        return total_trades, self.successful_trades, success_rate