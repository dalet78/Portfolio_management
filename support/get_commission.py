import backtrader as bt

class VolumeBasedCommission(bt.CommInfoBase):
    params = (
        ("commission_per_share", 0.0035),  # $0.0035 per azione
        ("min_commission", 0.35),  # Minimo $0.35 per ordine
        ("max_percentage", 0.01),  # Massimo 1% del valore del trade
    )

    def _getcommission(self, size, price, pseudoexec):
        # Calcola la commissione basata sulle azioni
        commission = abs(size) * self.p.commission_per_share

        # Imposta il massimo come 1% del valore della transazione
        max_commission = abs(size) * price * self.p.max_percentage

        # Applica il minimo di $0.35 per operazione
        return max(self.p.min_commission, min(commission, max_commission))