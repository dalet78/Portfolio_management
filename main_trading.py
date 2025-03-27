import subprocess
import sys

# Lista degli script da eseguire
scripts = [
    "sma_crossing_trading_strategies/sma_cros_candle_trading.py",
    "sma_crossing_trading_strategies/sma_cros_sma50_trading.py",
    "sma_crossing_trading_strategies/sma_cros_cents_trading.py",
    "sma_crossing_trading_strategies/sma_cros_combined_trading.py",
    "ema_crossing_trading_strategies/ema_cros_cents_trading.py",
    "ema_crossing_trading_strategies/ema_cros_candle_trading.py",
    "ema_crossing_trading_strategies/ema_cros_ema50_trading.py"
]

# Percorso base degli script
base_path = "/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Trading/strategies_order/"

# Lista dei processi attivi
processes = []

# Avvia gli script con output immediato
for script in scripts:
    script_path = base_path + script
    print(f"🚀 Avviando: {script_path}")

    process = subprocess.Popen(
        ["python", script_path],
        stdout=sys.stdout,  # Stampa direttamente l'output nel terminale
        stderr=sys.stderr
    )

    processes.append(process)
    print(f"🔹 {script} avviato con PID: {process.pid}")

# Attendi la conclusione di tutti gli script
for process in processes:
    process.wait()
