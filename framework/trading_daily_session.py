from datetime import datetime, timedelta
import time as tm
from support.logger import LoggerSingleton
from configuration.strategis_stock_applied import get_stock_list, get_all_check_functions, strategies_stock_applied
from libs.ibs_menager import IBOrderManager
from configuration import data_configuration_session
from Trading.strategies_order.ema_crossing_trading_strategies.ema_cros_ema50_trading import check_ema_cross_ema50
from Trading.strategies_order.ema_crossing_trading_strategies.ema_cros_candle_trading import check_ema_cross_candle
from Trading.strategies_order.sma_crossing_trading_strategies.sma_cros_sma50_trading import check_sma_cross_sma50
from Trading.strategies_order.sma_crossing_trading_strategies.sma_cros_candle_trading import check_sma_cross_candle
from Trading.strategies_order.vwap_trading_strategies.vwap_diff_trading import check_vwap_diff_signal
from Trading.strategies_order.vwap_trading_strategies.vwap_diff_trading_with_rsi import check_vwap_diff_signal_with_rsi
from Trading.strategies_order.vwap_trading_strategies.vwap_diff_trading_with_volume import check_vwap_diff_signal_with_volume

class TradingLoopManager:
    def __init__(self, ib_manager: IBOrderManager):
        self.ib_manager = ib_manager
        self.log = LoggerSingleton.get_logger()
        self.trade_tracker = TradeTracker()
        self._strategy_results = {}
        self._last_run_times = {}  # dict: strategy_name -> last_run_time
        self._last_sent_summary_per_stock = {}

    def trading_loop(self):
        reference_time = datetime.now().replace(second=0, microsecond=0)
        start_time = tm.time()  # Solo per logging o statistiche se vuoi

        strategy_list = get_all_check_functions()

        for check_function_name in strategy_list:
            strategy_name, tickers_list, strat_start_time, strat_stop_time, frequency, bar_size = (
                self._get_strategy_data_by_check_function(check_function_name, strategies_stock_applied))

            if not strategy_name:
                self.log.log(f"⚠️ Strategy not found for check function: {check_function_name}", level="warning")
                continue

            last_run = self._last_run_times.get(strategy_name, datetime.min)

            if (reference_time - last_run).total_seconds() >= frequency * 60:
                self._run_strategy_if_applicable(strategy_name, tickers_list, strat_start_time, strat_stop_time,
                                                 check_function_name, bar_size)
                self._last_run_times[strategy_name] = reference_time
            else:
                self.log.log(f"⏱ Skipping {strategy_name}, not yet time (every {frequency}m)", level="debug")

        self.log.log("📊 Updating SL/TP for active orders", level="info")
        self._update_active_orders()
        # self._check_and_update_trailing_sl()

        if hasattr(self, "telegram_bot"):
            summary_text, raw_data = self._format_open_positions_summary()

            for stock, line in raw_data.items():
                last_line = self._last_sent_summary_per_stock.get(stock)
                if line != last_line:
                    self.telegram_bot.send_telegram_message(line)
                    self._last_sent_summary_per_stock[stock] = line

        self._wait_until_next_iteration(reference_time)


    def _get_strategy_data_by_check_function(self, check_function_name, strategies_dict):
        for strat_name, strat_data in strategies_dict.items():
            if strat_data["check_function"] == check_function_name:
                return (
                    strat_name,
                    strat_data["tickers"],
                    strat_data["start_time"],
                    strat_data["stop_time"],
                    strat_data.get("frequency", 5),
                    strat_data.get("bar_size", "5 mins")
                )
        return None, [], None, None, 5, "5 mins"

    def _wait_until_next_iteration(self, reference_time):
        next_minute = reference_time + timedelta(minutes=1)
        now = datetime.now()

        if not isinstance(reference_time, datetime):
            self.log.log(f"❌ reference_time is not datetime: {type(reference_time)}", level="error")
            return

        sleep_time = (next_minute - now).total_seconds()

        if sleep_time > 0:
            self.log.log(f"⏳ Sleeping for {sleep_time:.2f} seconds before the next cycle", level="info")
            tm.sleep(sleep_time)
        else:
            self.log.log(f"⚠️ No sleep time, execution already late by {-sleep_time:.2f} seconds", level="warning")

    def _run_strategy_if_applicable(self, strategy_name, tickers_list, strat_start_time, strat_stop_time, check_function_name, bar_size):
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
        self._run_single_trading_iteration(strategy_name, tickers_list, check_signals, bar_size)

    def _run_single_trading_iteration(self, strategy_name, tickers_list, check_signals, bar_size):
        try:
            for ticker in tickers_list:
                # 🔒 Check se è consentito fare un trade
                if not self.trade_tracker.can_trade(stock=ticker):
                    self.log.log(f"🚫 Trade not allowed for {ticker} (limit reached)", stock=ticker, level="debug")
                    continue

                if self.trade_tracker.in_open_position(ticker):
                    self.log.log(f"🚫 Position already open for {ticker}, skipping new trade", stock=ticker,
                                 level="debug")
                    continue

                df, contract = self.ib_manager.get_stock_data(ticker, bar_size=bar_size)
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
        required_keys = {'entry_price', 'sl', 'tp', 'type'}
        raw_data = {}

        for stock, data in self.trade_tracker.open_positions.items():
            if not required_keys.issubset(data):
                self.log.log(f"⚠️ Missing required keys in open position data for {stock}: {data}", stock=stock,
                             level="warning")
                continue

            try:
                entry_price = round(data['entry_price'], 2)
                sl = round(data['sl'], 2)
                tp = round(data['tp'], 2)
                trade_type = data['type']
                line = f"• {stock} → {trade_type} @ {entry_price} | SL: {sl} | TP: {tp}"
                message_lines.append(line)
                raw_data[stock] = line
            except Exception as e:
                self.log.log(f"❌ Error formatting summary for {stock}: {e}", stock=stock, level="error")

        summary_text = "\n".join(message_lines) if len(message_lines) > 1 else ""
        return summary_text, raw_data

    # def _check_and_update_trailing_sl(self):
    #     """Aggiorna lo SL se il prezzo ha raggiunto +1% dal prezzo di ingresso."""
    #
    #     for stock, trade in self.trade_tracker.open_positions.items():
    #         if not all(k in trade for k in ("entry_price", "sl", "order_id")):
    #             continue
    #
    #         contract = self.ib_manager.get_contract(stock)
    #         if not contract:
    #             self.log.log(f"⚠️ Impossibile ottenere il contratto per {stock}", stock=stock, level="warning")
    #             continue
    #
    #         # Ottieni prezzo attuale di mercato
    #         ticker_data = self.ib_manager.ib.reqMktData(contract, "", False, False)
    #         self.ib_manager.ib.sleep(1)
    #         current_price = ticker_data.last if ticker_data.last else ticker_data.close
    #
    #         entry = trade["entry_price"]
    #         sl = trade["sl"]
    #
    #         # Se guadagno ≥ 1%, aggiorna SL
    #         if current_price >= entry * 1.01:
    #             new_sl = round(entry + 0.02, 2)
    #
    #             if new_sl > sl:
    #                 self.log.log(
    #                     f"🔄 Aggiornamento SL per {stock}: da {sl} a {new_sl} (entry: {entry}, current: {current_price})",
    #                     stock=stock, level="info"
    #                 )
    #
    #                 order_id = trade["order_id"]
    #                 # Aggiorna solo SL mantenendo TP invariato
    #                 self.ib_manager.set_tp_sl_direct_from_tracker(stock, order_id, new_sl, trade["tp"])
    #                 # Salva anche nel tracker
    #                 self.trade_tracker.open_positions[stock]["sl"] = new_sl

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
