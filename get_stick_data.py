import threading

from binance_f import RequestClient
from binance_f.model import *
from binance_f.constant.test import *
from binance_f.base.printobject import *
from datetime import datetime, timedelta
import talib.abstract as ta
import numpy as np


class MACD_RSI_machine():
	def __init__(self):
		self.price = []
		self.moving_avg_12 = 0
		self.moving_avg_26 = 0
		self.request_client = RequestClient(api_key="cGBSO4BJK7Mmlhxnp4wUAI56wgNGZH6DrZLOzd8i1rM52EExhhgbedSxq6gqy4Sh",
                                   secret_key="")

	def thread_run(self):
		self.run()
		threading.Timer(0.3, self.thread_run).start()

	def run(self):
		serverTime = self.request_client.get_servertime()
		#print("server time: ", datetime.fromtimestamp(serverTime / 1000))
		server_obj = datetime.fromtimestamp((serverTime / 1000))
		pTime = server_obj - timedelta(days=2)
		#print("one day ago : ", pTime)

		sticks = self.request_client.get_candlestick_data(symbol="BTCUSDT", interval=CandlestickInterval.MIN15,
													 startTime=pTime, endTime=serverTime, limit=50)

		#print("======= Kline/Candlestick Data =======")
		# PrintMix.print_data(type(result))
		for stick in sticks:
			self.price.append(float(stick.close))
			_time = datetime.fromtimestamp(stick.closeTime / 1000)
			#print(f'{_time} : {stick.close}')
		#print("======================================")
		print("from home")
		self.moving_avg_12 = sum(self.price[-12:]) / 12
		self.moving_avg_26 = sum(self.price[-26:]) / 26
		close_price_list_nparr = np.array(self.price, dtype='f8')

		rsi14 = ta.RSI(close_price_list_nparr,timeperiod = 14)
		print(f' avg12 : {round(self.moving_avg_12,4)}  avg26 : {round(self.moving_avg_26,4)}  rsi14 : {rsi14[-1]}')
		#print(len(self.price))
		print("hey")

if __name__ == '__main__':
	a = MACD_RSI_machine()
	#a.thread_run()
	a.thread_run()