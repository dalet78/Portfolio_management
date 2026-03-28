from ib_insync import *
import time
from datetime import datetime
import pandas as pd
import random
from support.logger import LoggerSingleton


class IBOrderManager:
    def __init__(self, host='127.0.0.1', port=7497, client_id=None):
        self.ib = IB()
        self.client_id = client_id if client_id is not None else random.randint(100, 999)

        self.log = LoggerSingleton.get_logger()
        self.pending_trades = {}

        try:
            self.connect_to_ib(host, port, self.client_id)  # ✅ Connessione sincrona
            self.log.log("✅ Connected to IBKR successfully", level="info")
        except Exception as e:
            self.log.log(f"❌ Connection failed: {e}", level="error")

    def connect_to_ib(self, host, port, client_id, retries=10, delay=10):
        for attempt in range(1, retries + 1):
            try:
                if not self.ib.isConnected():
                    self.ib.connect(host, port, clientId=client_id)
                    return
            except Exception as e:
                self.log.log(f"Attempt {attempt} failed: {e}", level="warning")
                time.sleep(delay)
        raise ConnectionError("❌ Unable to connect to IBKR after multiple attempts")

    def is_connected(self):
        """Return True if IBKR is connected, False otherwise."""
        return self.ib.isConnected()

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

    def place_order(self, symbol:str, action: str, quantity: int = 10,
                    order_type: str = "market", limit_price: float = None):
        """
        Place a market or limit order and track it in pending trades.

        :param contract: Stock contract (es. Stock('AAPL', 'SMART', 'USD'))
        :param action: "BUY" or "SELL"
        :param quantity: Numero di azioni da acquistare/vendere
        :param order_type: "market" per ordini a mercato, "limit" per ordini limite
        :param limit_price: Prezzo per l'ordine limite (necessario se order_type="limit")
        :return: Order ID
        """

        # ✅ Controllo che action sia una stringa corretta
        if not isinstance(action, str) or action.upper() not in ["BUY", "SELL"]:
            raise ValueError(f"❌ Invalid action: {action}. Must be 'BUY' or 'SELL'.")

        contract = Stock(symbol=symbol, exchange="SMART", currency="USD")
        self.ib.qualifyContracts(contract)

        if order_type.lower() == "market":
            order = MarketOrder(action.upper(), quantity)  # ✅ Garantisco che sia maiuscolo
            self.log.log(f"Placing MARKET order for {contract.symbol}: {quantity} shares", stock=contract.symbol)

        elif order_type.lower() == "limit":
            if limit_price is None:
                raise ValueError("❌ Limit price must be specified for limit orders.")
            order = LimitOrder(action.upper(), quantity, limit_price)
            self.log.log(f"Placing LIMIT order for {contract.symbol}: {quantity} shares at {limit_price}",
                         stock=contract.symbol)

        else:
            raise ValueError("❌ Invalid order type. Use 'market' or 'limit'.")

        # Invia l'ordine
        trade = self.ib.placeOrder(contract, order)

        # Memorizza l'ordine in pending_trades
        self.pending_trades[trade.order.orderId] = (trade, contract)

        return trade.order.orderId

    def update_orders(self, sl_tp_data):
        """
        Aggiorna gli ordini aperti e imposta SL/TP usando dati già calcolati.
        Parametri:
            sl_tp_data: dict {order_id: {"sl": ..., "tp": ...}}
        """
        self.ib.reqAllOpenOrders()
        self.ib.sleep(1)

        for order_id, trade_info in list(self.pending_trades.items()):
            if isinstance(trade_info, tuple) and len(trade_info) == 2:
                trade, contract = trade_info
            else:
                self.log.log(f"❌ Invalid trade_info format for order {order_id}: {trade_info}", level="error")
                continue

            trade.update()

            if trade.orderStatus.status == "Filled":
                self.log.log(f"✅ Order {order_id} filled at {trade.orderStatus.avgFillPrice}", level="info")

                # 🎯 Imposta SL/TP solo se i dati sono presenti
                sltp = sl_tp_data.get(order_id)
                if sltp:
                    sl = sltp.get("sl")
                    tp = sltp.get("tp")
                    self.set_tp_sl_direct(trade, sl_price=sl, tp_price=tp)
                else:
                    self.log.log(f"⚠️ No SL/TP found for order {order_id}, skipping.", level="warning")

                del self.pending_trades[order_id]

    def set_tp_sl_direct(self, trade, sl_price: float, tp_price: float):
        """Set SL/TP usando ordini OCA (One Cancels All), con TP come MIT e SL come STOP."""
        contract = trade.contract
        if not trade.order or not hasattr(trade.order, "action"):
            self.log.log(f"❌ Invalid trade object, missing 'order.action' for {contract.symbol}", level="error")
            return
        action = trade.order.action

        if not sl_price or not tp_price:
            self.log.log(f"⚠️ Missing SL or TP for {contract.symbol}, skipping.", level="warning")
            return

        sl_price = round(sl_price, 2)
        tp_price = round(tp_price, 2)
        # tp_limit_price = round(tp_price - 0.05, 2) if action == 'BUY' else round(tp_price + 0.05, 2)

        self.log.log(f"🔹 Setting TP (LMT) {tp_price} and SL {sl_price} for {contract.symbol}", level="info")

        opposite_action = 'SELL' if action == 'BUY' else 'BUY'
        quantity = trade.order.totalQuantity
        oca_group = f"OCA_{contract.symbol}_{int(time.time())}"


        # 🛡️ SL come Stop Order → transmit=False
        sl_order = StopOrder(
            action=opposite_action,
            totalQuantity=quantity,
            stopPrice=sl_price,
            ocaGroup=oca_group,
            ocaType=1,
            transmit=True
        )

        # 🎯 TP come STP LMT → transmit=True (ultimo ordine trasmette entrambi)
        tp_order = Order(
            action=opposite_action,
            orderType='LMT',
            totalQuantity=quantity,
            lmtPrice=tp_price,
            ocaGroup=oca_group,
            ocaType=1,
            transmit=True
        )

        # ⏱️ Invio ordini
        sl_trade = self.ib.placeOrder(contract, sl_order)
        tp_trade = self.ib.placeOrder(contract, tp_order)


        tp_trade.update()
        sl_trade.update()

        self.log.log(f"✅ TP (MIT) Order Status: {tp_trade.orderStatus.status} (Trigger: {tp_price})", level="info")
        self.log.log(f"✅ SL (Stop) Order Status: {sl_trade.orderStatus.status} (Trigger: {sl_price})", level="info")

    def close_position(self, contract):
        """Close an open position for the given contract."""
        try:
            # Recupera la posizione aperta
            positions = self.ib.positions()
            position = next((p for p in positions if p.contract.symbol == contract.symbol), None)

            if position:
                action = "SELL" if position.position > 0 else "BUY"
                quantity = abs(position.position)

                # ✅ Forza l'uso del router SMART
                contract.exchange = "SMART"
                contract.primaryExchange = "NASDAQ"  # opzionale ma consigliato
                contract.currency = "USD"

                self.log.log(f"🔹 Closing {quantity} shares of {contract.symbol} ({action})", stock=contract.symbol)

                order = MarketOrder(action, quantity)
                trade = self.ib.placeOrder(contract, order)

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

    def get_contract(self, symbol: str):
        """
        Returns a qualified IBKR Stock contract for a given symbol.
        """
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            return contract
        except Exception as e:
            self.log.log(f"❌ Failed to get contract for {symbol}: {e}", stock=symbol, level="error")
            return None

    def get_daily_trade_summary_with_pnl(self):
        """
        Restituisce un riepilogo leggibile dei trade eseguiti oggi con stima del PNL reale.
        Combina le esecuzioni del giorno con i dati aggiornati di portafoglio.
        """
        summary = ["📈 Daily Executed Trades with Real PNL:"]
        total_realized_pnl = 0.0
        today = datetime.now().date()

        # 🟢 Ottieni esecuzioni (oggetti Fill)
        executions = self.ib.fills()

        if not executions:
            return "📉 No trades executed today."

        found_trades = False

        for fill in executions:
            exec_time = pd.to_datetime(fill.time).tz_localize(None)
            if exec_time.date() != today:
                continue

            found_trades = True

            symbol = fill.contract.symbol
            action = fill.execution.side  # ✅ FIX
            qty = fill.execution.shares  # ✅ FIX
            price = round(fill.execution.price, 2)  # ✅ FIX
            order_id = fill.execution.orderId  # ✅ FIX

            summary.append(f"• {symbol} → {action} {qty} @ {price} [Order ID: {order_id}]")

        # 🔁 Richiesta aggiornamento del portafoglio
        accounts = self.ib.managedAccounts()
        if not accounts:
            self.log.log("❌ No managed accounts available", level="error")
            return "⚠️ No account found"

        account = accounts[0]
        self.ib.reqAccountUpdates(account)
        time.sleep(1)

        portfolio = self.ib.portfolio()

        for item in portfolio:
            if item.position == 0 and item.realizedPNL != 0.0:
                symbol = item.contract.symbol
                realized = round(item.realizedPNL, 2)
                total_realized_pnl += realized
                summary.append(f"• {symbol} → Realized PNL: {realized} USD")

        if not found_trades and total_realized_pnl == 0:
            return "📉 No trades executed today."

        summary.append(f"\n📊 Total Realized PNL: **{round(total_realized_pnl, 2)} USD**")
        return "\n".join(summary)

    def set_tp_sl_direct_from_tracker(self, stock: str, order_id: int, new_sl: float, tp: float):
        """
        Aggiorna SL/TP per un ordine esistente usando un nuovo gruppo OCA.
        Cancella eventuali ordini OCA precedenti associati al contratto.
        """
        contract = self.get_contract(stock)
        if not contract:
            self.log.log(f"❌ Cannot set SL/TP: contract not found for {stock}", stock=stock, level="error")
            return

        positions = self.ib.positions()
        position = next((p for p in positions if p.contract.symbol == stock), None)

        if not position:
            self.log.log(f"⚠️ No open position for {stock} found while setting SL/TP", stock=stock, level="warning")
            return

        action = "SELL" if position.position > 0 else "BUY"
        quantity = abs(position.position)

        # ✅ Cancella eventuali OCA esistenti
        open_trades = self.ib.trades()
        cancelled = 0
        for t in open_trades:
            if t.order.ocaGroup and t.contract.symbol == stock:
                self.ib.cancelOrder(t.order)
                cancelled += 1

        if cancelled:
            self.log.log(f"🗑️ Cancellati {cancelled} ordini OCA precedenti per {stock}", stock=stock, level="info")

        # ✅ Nuovo gruppo OCA
        oca_group = f"OCA_{stock}_{int(time.time())}"
        sl_order = StopOrder(
            action=action,
            totalQuantity=quantity,
            stopPrice=round(new_sl, 2),
            ocaGroup=oca_group,
            ocaType=1,
            transmit=False
        )
        tp_order = LimitOrder(
            action=action,
            totalQuantity=quantity,
            lmtPrice=round(tp, 2),
            ocaGroup=oca_group,
            ocaType=1,
            transmit=True
        )

        self.log.log(
            f"🔁 Updating SL to {new_sl} and keeping TP {tp} for {stock} (New OCA group: {oca_group})",
            stock=stock, level="info"
        )

        self.ib.placeOrder(contract, sl_order)
        self.ib.placeOrder(contract, tp_order)

