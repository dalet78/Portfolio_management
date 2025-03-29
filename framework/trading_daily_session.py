import time as tm
from datetime import datetime
from support.logger import Logger
from configuration.strategis_stock_applied import get_stock_list, get_all_check_functions, strategies_stock_applied
from libs.ibs_menager import IBOrderManager
from configuration import data_configuration_session
from Trading.strategies_order.ema_crossing_trading_strategies.ema_cros_ema50_trading import check_ema_cross_ema50
from Trading.strategies_order.ema_crossing_trading_strategies.ema_cros_candle_trading import check_ema_cross_candle
from Trading.strategies_order.sma_crossing_trading_strategies.sma_cros_sma50_trading import check_sma_cross_sma50
from Trading.strategies_order.sma_crossing_trading_strategies.sma_cros_candle_trading import check_sma_cross_candle
from Trading.strategies_order.vwap_trading_strategies.vwap_diff_trading import check_vwap_diff_signal

class TradingLoopManager:
    def __init__(self, ib_manager: IBOrderManager, log: Logger):
        self.ib_manager = ib_manager
        self.log = log
        self.trade_tracker = TradeTracker()
        self._strategy_results = {}

    def trading_loop(self):
        start_time = tm.time()
        strategy_list = get_all_check_functions()

        ### da modificare dizionario e modificare la funzione per ridare maggiori dati
        for check_function_name in strategy_list:
            strategy_name, tickers_list, strat_start_time, strat_stop_time = self._get_strategy_data_by_check_function(
                check_function_name, strategies_stock_applied)

            if not strategy_name:
                self.log.log(f"⚠️ Strategy not found for check function: {check_function_name}", level="warning")
                continue

            self._run_strategy_if_applicable(strategy_name, tickers_list, strat_start_time, strat_stop_time, check_function_name)

        self.log.log("📊 Updating SL/TP for active orders", level="info")
        self._update_active_orders()
        if hasattr(self, "telegram_bot"):  # Solo se il bot è stato collegato
            message = self._format_open_positions_summary()
            self.telegram_bot.send_telegram_message(message)
        self._wait_until_next_iteration(start_time)

    def _get_strategy_data_by_check_function(self, check_function_name, strategies_dict):
        for strat_name, strat_data in strategies_dict.items():
            if strat_data["check_function"] == check_function_name:
                return strat_name, strat_data["tickers"], strat_data["start_time"], strat_data["stop_time"]
        return None, [], None, None

    def _wait_until_next_iteration(self, start_time):
        execution_time = tm.time() - start_time
        sleep_time = 300 - execution_time
        if sleep_time > 0:
            self.log.log(f"⏳ Sleeping for {sleep_time:.2f} seconds before the next cycle", level="info")
            tm.sleep(sleep_time)
        else:
            self.log.log(f"⚠️ No sleep time, execution took {execution_time:.2f} seconds", level="warning")

    def _run_strategy_if_applicable(self, strategy_name, tickers_list, strat_start_time, strat_stop_time, check_function_name):
        current_time = datetime.now().time()

        if not (strat_start_time <= current_time <= strat_stop_time):
            self.log.log(
                f"⏰ Strategy '{strategy_name}' not executed because it's outside the time window: {strat_start_time} - {strat_stop_time}",
                level="info")
            return

        check_signals = globals().get(check_function_name)
        if check_signals is None:
            self.log.log(f"❌ Function not found: {check_function_name}", level="error")
            return

        self.log.log(f"🔄 Starting trading loop for strategy: {strategy_name}", level="info")
        print(f"\n🔄 Strategy: {strategy_name}")
        print(f"📈 Stocks to trade: {tickers_list}")
        self._run_single_trading_iteration(strategy_name, tickers_list, check_signals)

    def _run_single_trading_iteration(self, strategy_name, tickers_list, check_signals):
        try:
            for ticker in tickers_list:
                # 🔒 Check se è consentito fare un trade
                if not self.trade_tracker.can_trade(stock=ticker):
                    self.log.log(f"🚫 Trade not allowed for {ticker} (limit reached)", stock=ticker, level="debug")
                    continue

                df, contract = self.ib_manager.get_stock_data(ticker)
                if df is None:
                    continue

                result = check_signals(df, ticker, self.log, self.trade_tracker)

                if not isinstance(result, dict) or "signal" not in result:
                    self.log.log(f"❌ Invalid return format from check_signals for {ticker}: {result}", stock=ticker,
                                 level="error")
                    continue

                signal = result["signal"]
                self.log.log(f"🔍 Signal for {ticker}: {signal}", stock=ticker, level="debug")

                if not signal:
                    self.log.log(f"ℹ️ No valid signal for {ticker}", stock=ticker, level="info")
                    continue

                if signal not in ["BUY", "SELL"]:
                    self.log.log(f"❌ Invalid signal value for {ticker}: {signal}", stock=ticker, level="error")
                    continue

                last_price = df['close'].iloc[-1]
                quantity = int(data_configuration_session.CAPITAL_FOR_TRADE / last_price)

                order_id = self.ib_manager.place_order(ticker, signal, quantity, order_type=result["order_type"],
                                                       limit_price=result["entry_price"])
                if order_id:
                    # 🟢 Salva risultato
                    result_copy = result.copy()
                    result_copy["order_id"] = order_id
                    self._strategy_results[ticker] = result_copy

                    # 📌 Registra il trade in tracker
                    self.trade_tracker.register_trade(ticker, {
                        "type": signal,
                        "entry_price": result.get("entry_price", last_price),
                        "sl": result.get("sl"),
                        "tp": result.get("tp"),
                        "order_id": order_id,
                        "quantity": quantity,
                        "strategy": strategy_name,
                        "reason": result.get("reason")
                    })

                    self.log.log(f"✅ Order {signal} for {ticker} placed with ID {order_id}", stock=ticker, level="info")
                else:
                    self.log.log(f"⚠️ Order for {ticker} failed", stock=ticker, level="warning")

        except Exception as e:
            self.log.log(f"❌ Error in trading iteration for {strategy_name}: {e}", level="error")

    def _update_active_orders(self):
        sl_tp_data = {
            trade["order_id"]: {"sl": trade["sl"], "tp": trade["tp"]}
            for trade in self.trade_tracker.open_positions.values()
            if all(k in trade for k in ("order_id", "sl", "tp"))
        }

        self.ib_manager.update_orders(sl_tp_data=sl_tp_data)

    def _close_all_positions(self):
        """Chiude tutte le posizioni registrate nel TradeTracker."""
        for stock, trade_data in self.trade_tracker.open_positions.items():
            contract = self.ib_manager.get_contract(stock)
            if contract:
                self.ib_manager.close_position(contract)
            else:
                self.log.log(f"⚠️ Unable to retrieve contract for {stock}", stock=stock, level="warning")

    def _format_open_positions_summary(self):
        message_lines = ["📊 Open Trades Summary:"]
        for stock, data in self.trade_tracker.open_positions.items():
            line = f"• {stock} → {data['type']} @ {round(data['entry'], 2)} | SL: {round(data['sl'], 2)} | TP: {round(data['tp'], 2)}"
            message_lines.append(line)
        return "\n".join(message_lines) if len(message_lines) > 1 else "No open trades."

class TradeTracker:
    def __init__(self):
        self.open_positions = {}
        self.trade_count_per_stock = {}
        self.total_trades = 0
        self.max_trades_per_stock = data_configuration_session.MAX_TRADES_PER_STOCK
        self.max_daily_trades = data_configuration_session.MAX_DAILY_TRADES

    def in_open_position(self, stock):
        return stock in self.open_positions

    def max_trades_reached_for_stock(self, stock):
        return self.trade_count_per_stock.get(stock, 0) >= self.max_trades_per_stock

    def max_daily_trades_reached(self):
        return self.total_trades >= self.max_daily_trades

    def can_trade(self, stock):
        """Check if a trade is allowed for this stock and for the day."""
        return (
            not self.in_open_position(stock) and
            not self.max_trades_reached_for_stock(stock) and
            not self.max_daily_trades_reached()
        )

    def register_trade(self, stock, position_info=None):
        self.trade_count_per_stock[stock] = self.trade_count_per_stock.get(stock, 0) + 1
        self.total_trades += 1
        if position_info:
            self.open_positions[stock] = position_info
