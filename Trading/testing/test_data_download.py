from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # Usa 7496 per live trading

# Verifica il tipo di dati disponibili
ib.reqMarketDataType(3)  # 1 = real-time, 3 = delayed, 4 = delayed frozen

contract = Stock("INTC", "SMART", "USD")
ticker = ib.reqMktData(contract)

ib.sleep(2)  # Aspetta per ricevere i dati

# Controlla se ricevi dati
if ticker.last:
    print(f"Last price received: {ticker.last}")
else:
    print("No market data received. You may not have the required subscription.")

ib.disconnect()
