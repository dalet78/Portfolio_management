
from configuration.strategis_stock_applied import get_stock_list
from support.logger import Logger
from libs.ibs_menager import IBOrderManager

def buy_signals():
    ib_manager = IBOrderManager()
    symbol = "WBD"
    signal = "BUY"
    quantity= 10
    order_id = ib_manager.place_order(symbol, signal, quantity)

if __name__ == "__main__":
    buy_signals()