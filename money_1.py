import ccxt
from datetime import datetime
binance = ccxt.binance({
    'apiKey': 'kyaqcDNfq5aWhzbcH263eVHjGOW8y3MmL2scp1pIjLbzvdoWorQv0tP3oHbW2VoX',
    'secret': '',
})
ohlcvs = binance.fetch_ohlcv('ETH/BTC')

for ohlc in ohlcvs:
    print(datetime.fromtimestamp(ohlc[0]/1000).strftime('%Y-%m-%d %H:%M:%S'))

balance = binance.fetch_balance()
print(balance.keys())
print(balance['total'])