from ib_insync import IB
from datetime import datetime
import time
from libs.ibs_menager import IBOrderManager
from support.logger import LoggerSingleton

daily_date = datetime.now().strftime("%d_%m_%y__%H_%M")
log_path = f"/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/daily_tading_{daily_date}.log"
log = LoggerSingleton.get_logger(log_path)

# ✅ Inizializza
manager = IBOrderManager()

# ✅ Passo 1: Simula un ordine MARKET BUY su AAPL
order_id = manager.place_order(symbol='WBD', action='BUY', quantity=1, order_type='market')

# ✅ Passo 2: Attendi che l'ordine venga riempito
time.sleep(3)
manager.update_orders({
    order_id: {
        "sl": 7.50,     # stop loss
        "tp": 9.30      # take profit
    }
})

# ✅ Passo 3: Controlla che SL/TP siano stati piazzati
manager.check_open_orders()
