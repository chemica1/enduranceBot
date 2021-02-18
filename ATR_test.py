import threading, time
from datetime import datetime, timedelta
from binance_f import RequestClient
from binance_f.model import *
import talib.abstract as ta
import numpy as np
from binance_f.constant.test import *
from binance_f.base.printobject import *

class machine():
    def __init__(self):
        self.request_client = RequestClient(api_key="", secret_key="")
        self.price_high = []
        self.price_low = []
        self.price_close = []

    def thread_run(self):
        serverTime = self.request_client.get_servertime()
        server_obj = datetime.fromtimestamp((serverTime / 1000))
        pTime = server_obj - timedelta(days=2)

        sticks = self.request_client.get_candlestick_data(symbol="BTCUSDT", interval=CandlestickInterval.MIN15,
                                                          startTime=pTime, endTime=serverTime, limit=50)

        self.price_high.clear()
        self.price_low.clear()
        self.price_close.clear()

        for stick in sticks:
            self.price_high.append(float(stick.high))
            self.price_low.append(float(stick.low))
            self.price_close.append(float(stick.close))

        self.get_ATR()

        threading.Timer(1, self.thread_run).start()


    def get_ATR(self):
        price_high_np = np.array(self.price_high, dtype='f8')
        price_low_np = np.array(self.price_low, dtype='f8')
        price_close_np = np.array(self.price_close, dtype='f8')

        real = ta.ATR(price_high_np, price_low_np, price_close_np, timeperiod=14)
        print(f'ATR high : {self.price_close[-1] + (real[-1]*2)}  ATR low : {self.price_close[-1] - (real[-1]*2)}')

if __name__ == '__main__':
    a = machine()
    a.thread_run()