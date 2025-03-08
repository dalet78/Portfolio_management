import subprocess
import logging


def start_trading():
    """Avvia gli script di trading in parallelo."""
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    base_path = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Trading/strategies_order/"

    scripts = [
        base_path + "ema_crossing_trading_strategies/ema_cros_candle_trading.py",
        base_path + "ema_crossing_trading_strategies/ema_cros_ema50_trading.py",
        base_path + "sma_crossing_trading_strategies/sma_cros_candle_trading.py",
        base_path + "sma_crossing_trading_strategies/sma_cros_sma50_trading.py",
        base_path + "sma_crossing_trading_strategies/ema_cros_cents_trading.py",
        base_path + "sma_crossing_trading_strategies/ema_cros_combined_trading.py",
        base_path + "ema_crossing_trading_strategies/ema_cros_cents_trading.py",
    ]

    processes = []

    for script in scripts:
        try:
            logger.info(f"Avvio dello script: {script}")
            process = subprocess.Popen(["python", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append(process)
        except Exception as e:
            logger.error(f"Errore nell'avvio di {script}: {e}")

    for p in processes:
        stdout, stderr = p.communicate()
        if stdout:
            logger.info(stdout.decode())
        if stderr:
            logger.error(stderr.decode())
