import threading, time, File_class
from binance_f import RequestClient
from binance_f.model import *
import talib.abstract as ta
import numpy as np
from keys import keys
from File_class import File_class


class dogpig():
    def __init__(self):
        self.File_class = File_class('2020_05')
        api_key = keys()
        self.price_sticks_arr = []
        self.rsi14 = 0
        self.request_client = RequestClient(api_key=api_key.api_key(), secret_key="")
        self.position_flag = 0 #현재 포지션 flag. 0은 무포 1은 숏. // 숏봇은 hist가 양수에서 음수로 바뀔때 숏 진입한다
        self.short_flag = 3 # 이전에 hist가 양수였으면 0 // 음수였으면 1 // 첫 시작은 3
        self.stop_threading = False
        self.trade_var()

    def thread_run(self):
        self.run()
        if not self.stop_threading == True:
            threading.Timer(0.5, self.thread_run).start()

    def run(self):
        self.price_sticks_arr = self.get_sticks_arr(1)
        rsi14_1 = self.get_rsi(self.get_sticks_arr(1))

        MACD, MACDsignal, MACDhist = self.get_MACD_etc(self.price_sticks_arr)

        if self.position_flag == 0 :
            if MACDhist[-1] < 0 and self.short_flag == 0:
                self.stop_threading = True
                time.sleep(10)
                self.stop_threading = False
                self.position_flag = 1
                self.short_flag = 1
            if MACDhist[-1] > 0 :
                self.stop_threading = True
                time.sleep(10)
                self.stop_threading = False
                self.short_flag = 0

        elif self.position_flag == 1 :
            if MACDhist[-1] > 0 and self.short_flag == 1:
                print(f'숏 청산 {self.price_sticks_arr[-1]}')
                #추가함 수정 or 지워
                #
                current_price = self.get_market_price()
                #File_class.save_list(self.trade_out(float(current_price),'short')) //ZeroDivisionError: float division by zero 에러 떳다 자러 감 숙오
                # 추가함 수정 or 지워
                self.stop_threading = True
                time.sleep(10)
                self.stop_threading = False
                self.position_flag = 0
                self.short_flag = 0


    def get_sticks_arr(self, stick_time):
        tmp_sticks = []
        sticks = []
        if stick_time == 15:
            sticks = self.request_client.get_candlestick_data(symbol="BTCUSDT", interval=CandlestickInterval.MIN15,
                                                              startTime=None, endTime=self.request_client.get_servertime(),
                                                              limit=50)
        elif stick_time == 1 :
            sticks = self.request_client.get_candlestick_data(symbol="BTCUSDT", interval=CandlestickInterval.MIN1,
                                                              startTime=None,
                                                              endTime=self.request_client.get_servertime(),
                                                              limit=50)
        elif stick_time == 5:
            sticks = self.request_client.get_candlestick_data(symbol="BTCUSDT", interval=CandlestickInterval.MIN5,
                                                              startTime=None,
                                                              endTime=self.request_client.get_servertime(),
                                                              limit=50)
        for stick in sticks:
            tmp_sticks.append(float(stick.close))
            #_time = datetime.fromtimestamp(stick.closeTime / 1000)
            #print(f'{_time} : {stick.close}') #stick들의 데이터 프린트
        return tmp_sticks


    def trade_in(self, current_price):
        if self.position_flag == 1: #들어가있는가?
            print("잘못된 진입입니다. 이미 포지션이 있습니다.")
            return -1
        else:
            self.entrance_price = current_price

    def trade_out(self, current_price, position):
        if self.position_flag == 0: #포지션이 없는가?
            print("잘못된 청산입니다. 포지션이 없습니다.")
            return -1
        else:
            if position == 'short':
                percentage = (self.entrance_price - current_price)/self.entrance_price
                return percentage  #차익 퍼센트 리턴
            elif position == 'long':
                percentage = (current_price - self.entrance_price)/self.entrance_price
                return percentage  # 차익 리턴

    def trade_var(self):
        self.entrance_price = 0
        self.trading_history = 0

    def get_rsi(self, arr):
        close_price_list_nparr = np.array(arr, dtype='f8')
        rsi14 = ta.RSI(close_price_list_nparr, timeperiod = 14)
        return rsi14

    def get_MACD_etc(self, arr):
        close_price_list_nparr = np.array(arr, dtype='f8')
        macd, macdsignal, macdhist = ta.MACD(close_price_list_nparr, fastperiod=12, slowperiod=26, signalperiod=9)
        return macd, macdsignal, macdhist
    #추가함 수정 or 지워
    def get_market_price(self):
        result = self.request_client.get_mark_price(symbol="BTCUSDT")
        #print(result.markPrice)
        return result.markPrice


if __name__ == '__main__':
    a = dogpig()
    a.thread_run()


'''
    def run(self):
        serverTime = self.request_client.get_servertime()
        server_obj = datetime.fromtimestamp((serverTime / 1000))
        pTime = server_obj - timedelta(days=1)
        # print("one day ago : ", pTime)
'''