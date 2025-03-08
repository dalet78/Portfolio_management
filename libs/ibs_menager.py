from ib_insync import *
import random
from support.logger import Logger

class IBOrderManager:
    def __init__(self, host='127.0.0.1', port=7497, client_id=random.randint(100, 999),
                 log_path="/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Reports/logs/trading_debug.log"):
        """Initialize IBKR connection and logger."""
        self.ib = IB()
        self.ib.connect(host, port, client_id)
        self.log = Logger(log_path)
        self.log.log("Connected to IBKR", level="info")

        self.pending_trades = {}  # Store pending trades to track updates

    def get_stock_data(self, symbol:str, end_time:str=None, duration:str='2 D', bar_size:str="5 mins"):
        """Request historical data for the stock and return a DataFrame."""
        self.log.log(f"Requesting data for {symbol}", stock=symbol)
        contract = Stock(symbol, 'SMART', 'USD')
        try:
            self.ib.qualifyContracts(contract)
            bars = self.ib.reqHistoricalData(
                contract, endDateTime=end_time, durationStr=duration,
                barSizeSetting=bar_size, whatToShow='TRADES', useRTH=True
            )
            df = util.df(bars)

            if not df.empty:
                self.log.log(f"Data received for {symbol}: {len(df)} rows", stock=symbol)
            else:
                self.log.log(f"No data received for {symbol}", stock=symbol, level="warning")

            return df, contract
        except Exception as e:
            self.log.log(f"Error retrieving data: {e}", stock=symbol, level="error")
            return None, None

    def place_order(self, contract: Stock, action: str, quantity: int = 10,
                    sl_percent: float = 0.007, tp_percent: float = 0.014,
                    order_type: str = "market", limit_price: float = None):
        """
        Place a market or limit order and track it in pending orders.

        :param contract: Stock contract (es. Stock('AAPL', 'SMART', 'USD'))
        :param action: "BUY" or "SELL"
        :param quantity: Numero di azioni da acquistare/vendere
        :param sl_percent: Stop Loss in percentuale
        :param tp_percent: Take Profit in percentuale
        :param order_type: "market" per ordini a mercato, "limit" per ordini limite
        :param limit_price: Prezzo per l'ordine limite (necessario se order_type="limit")
        :return: Order ID
        """

        self.ib.qualifyContracts(contract)

        if order_type.lower() == "market":
            order = MarketOrder(action, quantity)
            self.log.log(f"Placing MARKET order for {contract.symbol}: {quantity} shares", stock=contract.symbol)

        elif order_type.lower() == "limit":
            if limit_price is None:
                raise ValueError("Limit price must be specified for limit orders.")
            order = LimitOrder(action, quantity, limit_price)
            self.log.log(f"Placing LIMIT order for {contract.symbol}: {quantity} shares at {limit_price}",
                         stock=contract.symbol)

        else:
            raise ValueError("Invalid order type. Use 'market' or 'limit'.")

        # Invia l'ordine
        trade = self.ib.placeOrder(contract, order)

        # Memorizza l'ordine in pending_trades
        self.pending_trades[trade.order.orderId] = (trade, contract)

        return trade.order.orderId

    def update_orders(self, sl_percent, tp_percent):
        """Update the status of all pending orders and check if they are filled."""
        self.ib.reqAllOpenOrders()
        self.ib.sleep(1)

        for order_id, trade_info in list(self.pending_trades.items()):
            print(f"DEBUG: Processing order_id {order_id}, trade_info = {trade_info}")

            if isinstance(trade_info, tuple) and len(trade_info) == 2:
                trade, contract = trade_info  # 🔹 Corretto!
            else:
                print(f"❌ Errore: trade_info ha un formato inatteso: {trade_info}")
                continue  # Saltiamo questo elemento se il formato non è corretto

            trade.update()
            if trade.orderStatus.status == "Filled":
                self.log.log(f"✅ Order {order_id} filled at {trade.orderStatus.avgFillPrice}", level="info")
                self.set_tp_sl(trade, sl_percent, tp_percent)  # 🔹 Correggi anche qui!
                del self.pending_trades[order_id]

    def set_tp_sl(self, trade, sl_percent:float, tp_percent:float):
        """Set Take Profit and Stop Loss after the order is executed."""
        contract = trade.contract
        filled_price = trade.orderStatus.avgFillPrice
        action = trade.order.action

        if filled_price == 0:
            self.log.log(f"⚠️ Warning: Filled price for {contract.symbol} is 0. TP/SL not placed.", level="warning")
            return

        sl_price = round(filled_price * (1 - sl_percent), 2) if action == 'BUY' else round(
            filled_price * (1 + sl_percent), 2)
        tp_price = round(filled_price * (1 + tp_percent), 2) if action == 'BUY' else round(
            filled_price * (1 - tp_percent), 2)

        self.log.log(f"🔹 Setting TP {tp_price} and SL {sl_price} for {contract.symbol}", level="info")

        take_profit_order = LimitOrder('SELL' if action == 'BUY' else 'BUY', trade.order.totalQuantity, tp_price)
        stop_loss_order = StopOrder('SELL' if action == 'BUY' else 'BUY', trade.order.totalQuantity, sl_price)

        tp_trade = self.ib.placeOrder(contract, take_profit_order)
        self.ib.sleep(1)
        sl_trade = self.ib.placeOrder(contract, stop_loss_order)
        self.ib.sleep(1)

        tp_trade.update()
        sl_trade.update()

        self.log.log(f"✅ TP Order Status: {tp_trade.orderStatus.status} (Price: {tp_price})", level="info")
        self.log.log(f"✅ SL Order Status: {sl_trade.orderStatus.status} (Price: {sl_price})", level="info")

    def close_position(self, contract):
        """Close an open position for the given contract."""
        try:
            # Recupera la posizione aperta
            positions = self.ib.positions()
            position = next((p for p in positions if p.contract.symbol == contract.symbol), None)

            if position:
                action = "SELL" if position.position > 0 else "BUY"  # Se long, vendi. Se short, compra
                quantity = abs(position.position)

                self.log.log(f"🔹 Closing {quantity} shares of {contract.symbol} ({action})", stock=contract.symbol)

                order = MarketOrder(action, quantity)
                trade = self.ib.placeOrder(contract, order)

                # Aspetta l'aggiornamento dello stato dell'ordine
                self.ib.sleep(1)
                trade.update()

                if trade.orderStatus.status == "Filled":
                    self.log.log(f"✅ Closed position for {contract.symbol} at {trade.orderStatus.avgFillPrice}",
                                 stock=contract.symbol)
                else:
                    self.log.log(f"⚠️ Order to close {contract.symbol} is {trade.orderStatus.status}",
                                 stock=contract.symbol, level="warning")
            else:
                self.log.log(f"⚠️ No open position found for {contract.symbol}", stock=contract.symbol, level="warning")

        except Exception as e:
            self.log.log(f"❌ Error closing position for {contract.symbol}: {e}", stock=contract.symbol, level="error")

    def check_open_orders(self):
        """Prints all open orders (including TP and SL) to verify they are set correctly."""
        open_orders = self.ib.reqOpenOrders()
        if not open_orders:
            print("❌ No open orders found (Check if TP/SL were placed correctly).")
            return

        print("\n🔎 **Checking Open Orders (TP/SL)**:")
        for trade in open_orders:
            order = trade.order
            print(
                f"➡️ Order {order.orderId}: {order.action} {order.totalQuantity} @ "
                f"{order.lmtPrice if order.orderType == 'LMT' else order.auxPrice} ({order.orderType})"
            )

    def check_trade_history(self):
        """Check if TP/SL orders have been executed."""
        print("\n🔎 **Checking Trade History (Executed TP/SL Orders):**")
        for trade in self.ib.trades():
            order = trade.order
            print(f"➡️ Trade {trade.order.orderId}: {order.action} {order.totalQuantity} @ {trade.orderStatus.avgFillPrice} ({order.orderType}) - Status: {trade.orderStatus.status}")
