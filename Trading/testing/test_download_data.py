from ib_insync import *
import pandas as pd

# Connessione a TWS
ib = IB()
ib.connect('127.0.0.1', 7496, clientId=1)  # Usa 4002 per IB Gateway

# Definizione del titolo (esempio: AAPL su NASDAQ)
contract = Stock('AAPL', 'SMART', 'USD')

# Richiesta dati storici (1 giorno di dati con candele da 5 minuti)
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='5 mins',
    whatToShow='TRADES',
    useRTH=True,
    formatDate=1
)

# Converti in DataFrame e salva in CSV
df = util.df(bars)
df.to_csv('/home/dp/PycharmProjects/Portfolio_management/Portfolio_management/Data/aapl_data_test.csv', index=False)

print("Dati salvati in aapl_data.csv")

# Disconnessione
ib.disconnect()
