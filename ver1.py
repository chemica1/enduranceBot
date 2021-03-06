import threading, time
from datetime import datetime, timedelta
from binance_f import RequestClient
from binance_f.model import *
import talib.abstract as ta
import numpy as np
from keys import keys
#from File_class import File_class
from binance_f.constant.test import *
from binance_f.base.printobject import *

class machine():
    def __init__(self):
        api_key = keys()
        self.request_client = RequestClient(api_key=api_key.api_key(), secret_key="")
        #self.File_class = File_class('2020_05')
        self.init_vars()
        self.init_status_bools()
        self.init_signals_bools()
        self.init_position_bools()
        self.init_threads()

    def init_vars(self):
        self.my_money = 1000
        self.now_price = 0
        self.close_price_1m = 0
        self.entrance_price = 0
        self.trading_history = 0
        self.newCandleStickArr_1m = []
        self.closePriceNpArr_1m = []
        self.position_flag = 0 #현재 포지션 flag. 0은 무포 1은 숏 2는 롱 // 숏봇은 hist가 양수에서 음수로 바뀔때 숏 진입한다
        self.short_flag = 3 # 이전에 hist가 양수였으면 0 // 음수였으면 1 // 첫 시작은 3
        self.avg_15m_20 =0

    def init_status_bools(self):
        self.closePer1m_is_it_updated = False #1분마다 종가 업뎃됐는지 확인
        self.RSI_is_it_above_X = False #RSI 기준치 설정
        self.RSI_is_it_below_X = False #RSI 기준치 설정
        self.ATR_15m_is_it_above_X = False
        self.ATR_15m_is_it_below_X = False

    def init_signals_bools(self):
        self.MACD_short_signal = False
        self.MACD_long_signal = False
        self.MACD_tradeOut_signal = False
        self.ATR_tradeOut_signal = False

    def init_position_bools(self):
        self.position_is_it_empty = True
        self.position_is_it_long = False
        self.position_is_it_short = False
        self.ATR_long_position = False
        self.ATR_short_position = False

    def init_threads(self):
        self.update_candlestickArr_1m_and_checking_MACDhist_per1s_thr()
        self.update_candlestickArr_15m_and_checking_ATR_per1s_thr()
        self.update_RSI_per3s_status_thr()
        self.update_ATR_position_tradeOut_signal_per1s_thr()
        self.main_thr()
        print(f'{(60 - datetime.now().second)}초 후, 1분봉 종가 업데이트 쓰레드가 시작됩니다.')
        threading.Timer((60-datetime.now().second), self.update_closePrice_per1m_thr).start()

    def trade_in(self, position, signal=''):
        self.del_signal(signal)
        if self.position_is_it_long == True or self.position_is_it_short == True:
            print("잘못된 진입입니다. 이미 포지션이 있습니다.")
            return -1
        else:
            if position == 'long' and self.position_is_it_empty == True:
                self.entrance_price = self.now_price
                self.position_is_it_long = True
                self.position_is_it_empty = False
                self.position_is_it_short = False
                print(f'{datetime.now()}  롱 포지션에 진입하였습니다. 현재가 : {self.now_price}')
                self.MACD_long_signal = False
            elif position == 'short' and self.position_is_it_empty == True:
                self.entrance_price = self.now_price
                self.position_is_it_short = True
                self.position_is_it_empty = False
                self.position_is_it_long = False
                print(f'{datetime.now()}  숏 포지션에 진입하였습니다. 현재가 : {self.now_price}')
                self.MACD_short_signal = False

    def trade_out(self):
        if self.position_is_it_empty == True: #포지션이 없는가?
            print("잘못된 청산입니다. 포지션이 없습니다.")
            return -1
        else:
            if self.position_is_it_short == True:
                self.position_is_it_short = False
                self.position_is_it_empty = True
                percentage = (self.entrance_price - self.now_price)/self.entrance_price
                self.my_money += self.my_money*percentage*20
                print(f'{datetime.now()}  숏 포지션을 청산하였습니다. 현재가 : {self.now_price}, 차익 {percentage*100*20}%, 현재 지갑 {self.my_money}')
            elif self.position_is_it_long == True:
                self.position_is_it_long = False
                self.position_is_it_empty = True
                percentage = (self.now_price - self.entrance_price )/self.entrance_price
                self.my_money += self.my_money*percentage*20
                print(f'{datetime.now()}  롱 포지션을 청산하였습니다. 현재가 : {self.now_price}, 차익 {percentage*100*20}%, 현재 지갑 {self.my_money}')

    def checking_MACDhist(self):
        macd_arr, macdsignal_arr, macdhist_arr = ta.MACD(self.closePriceNpArr_1m, fastperiod=12, slowperiod=26, signalperiod=9)
        if macd_arr[-1] < 0 and macdsignal_arr[-1] < 0:
            if macdhist_arr[-2] < 0 and macdhist_arr[-1] > 0:
                self.MACD_long_signal = True
            elif (abs(macdhist_arr[-3]) + abs(macdhist_arr[-2]) + abs(macdhist_arr[-1]))/3 > 1 and macdhist_arr[-2] > 0 and macdhist_arr[-1] - 2 < 0:
                self.MACD_tradeOut_signal = True
        elif macd_arr[-1] > 0 and macdsignal_arr[-1] > 0:
            if macdhist_arr[-2] > 0 and macdhist_arr[-1] < 0:
                self.MACD_short_signal = True
            elif (abs(macdhist_arr[-3]) + abs(macdhist_arr[-2]) + abs(macdhist_arr[-1]))/3 > 1 and macdhist_arr[-2] < 0 and macdhist_arr[-1] + 2 > 0:
                self.MACD_tradeOut_signal = True

    def main_thr(self):
        if self.closePer1m_is_it_updated ==True:
            print(f'{datetime.now()} : 종가가 업데이트 됐으므로 알고리즘 작동')
            self.closePer1m_is_it_updated = False

            if self.ATR_15m_is_it_below_X == True or self.ATR_15m_is_it_above_X == True: #ATR상향? 하향? 돌파를 먼저 판단하고
                if self.ATR_long_position == False and self.ATR_short_position == False: #상향 하향 돌파했는데도 ATR포지션이 아무것도 없다면 진입해야할 상황인 것.
                    self.trade_out() # 현재 포지션이 있다면 청산하고
                    if self.ATR_15m_is_it_below_X == True: # 하향돌파면
                        print(f'{datetime.now()} : ATR 하향돌파 매매')
                        self.trade_in('short') #숏 진입
                        self.ATR_short_position = True #ATR 숏진입은 특수상황이므로 기록
                        self.ATR_long_position = False
                    elif self.ATR_15m_is_it_above_X ==True: # 상향돌파면
                        print(f'{datetime.now()} : ATR 상향돌파 매매')
                        self.trade_in('long') #롱 진입
                        self.ATR_long_position = True #ATR 롱진입은 특수상황이므로 기록
                        self.ATR_short_position = False

            if self.ATR_long_position == True: #현재 포지션이 ATR 특수상황인지 판단
                if self.ATR_tradeOut_signal == True:
                    self.ATR_tradeOut_signal = False
                    self.ATR_long_position = False
                    self.trade_out()

            elif self.ATR_short_position == True: #현재 포지션이 ATR 특수상황인지 판단
                if self.ATR_tradeOut_signal == True:
                    self.ATR_tradeOut_signal = False
                    self.ATR_short_position = False
                    self.trade_out()

            if self.ATR_short_position == False and self.ATR_long_position == False: #위 ATR 특수상황이 아니라면 기존대로 MACD
                if self.position_is_it_empty == True:
                    if self.RSI_is_it_above_X == True and self.MACD_short_signal == True:
                        self.trade_in('short', 'MACD_short_signal')
                    if self.RSI_is_it_below_X == True and self.MACD_long_signal == True:
                        self.trade_in('long', 'MACD_long_signal')
                elif self.position_is_it_long == True:
                    if self.MACD_short_signal == True:
                        self.trade_out()
                    elif self.MACD_tradeOut_signal == True:
                        self.trade_out()
                elif self.position_is_it_short == True:
                    if self.MACD_long_signal == True:
                        self.trade_out()
                    elif self.MACD_tradeOut_signal == True:
                        self.trade_out()

        threading.Timer(1, self.main_thr).start()

    def checking_ATR(self):
        price_high = []
        price_low = []
        price_close = []

        for stick in self.newCandleStickArr_15m:
            price_high.append(float(stick.high))
            price_low.append(float(stick.low))
            price_close.append(float(stick.close))

        price_high_np = np.array(price_high, dtype='f8')
        price_low_np = np.array(price_low, dtype='f8')
        price_close_np = np.array(price_close, dtype='f8')

        real = ta.ATR(price_high_np, price_low_np, price_close_np, timeperiod=15)

        sum_15m_20 = 0
        for price in self.newCandleStickArr_15m[-20:]:
            sum_15m_20 += float(price.close)
        self.avg_15m_20 = sum_15m_20 / 20

        high = self.avg_15m_20 + (float(real[-1]) * 2)
        low = self.avg_15m_20 - (float(real[-1]) * 2)

        # 상방 돌파
        if self.now_price >= high:
            self.ATR_15m_is_it_above_X = True
            self.ATR_15m_is_it_below_X = False
        # 하방 돌파
        elif self.now_price <= low:
            self.ATR_15m_is_it_below_X = True
            self.ATR_15m_is_it_above_X = False
        # 중앙
        elif self.now_price < high and self.now_price > low:
            self.ATR_15m_is_it_above_X = False
            self.ATR_15m_is_it_below_X = False

    def update_candlestickArr_15m_and_checking_ATR_per1s_thr(self):
        try:
            tmp_Arr = self.request_client.get_candlestick_data(symbol="BTCUSDT",
                                                               interval=CandlestickInterval.MIN15,
                                                               startTime=None,
                                                               endTime=self.request_client.get_servertime(),
                                                               limit=50)
            self.newCandleStickArr_15m = tmp_Arr
            self.checking_ATR()

        except Exception as e:
            print(f'에러 : {e}')
        threading.Timer(1, self.update_candlestickArr_15m_and_checking_ATR_per1s_thr).start()

    def update_candlestickArr_1m_and_checking_MACDhist_per1s_thr(self):
        try:
            tmp_Arr = self.request_client.get_candlestick_data(symbol="BTCUSDT",
                                                               interval=CandlestickInterval.MIN1,
                                                               startTime=None,
                                                               endTime=self.request_client.get_servertime(),
                                                               limit=50)
            self.newCandleStickArr_1m = tmp_Arr
            self.now_price = float(self.newCandleStickArr_1m[-1].close)
            trash_Arr  =[]
            for stick in self.newCandleStickArr_1m:
                trash_Arr.append(float(stick.close))
            self.closePriceNpArr_1m = np.array(trash_Arr, dtype='f8')
            self.checking_MACDhist()
        except:
            print("인터넷 연결 / 서버 확인 필요")
        threading.Timer(1, self.update_candlestickArr_1m_and_checking_MACDhist_per1s_thr).start()

    def update_RSI_per3s_status_thr(self):
        X_low = 35
        X_high = 65
        waitingTime = 20
        RSI = ta.RSI(self.closePriceNpArr_1m, timperiod = 14)[-1]
        if RSI < X_low:
            self.RSI_is_it_below_X = True
            self.RSI_is_it_above_X = False
            print(f'{datetime.now()}  현재 RSI : {RSI}, {waitingTime}분간 롱 진입 대기, RSI_is_it_below_X = {self.RSI_is_it_below_X} ')
            time.sleep(60*waitingTime)
        elif RSI >= X_high and RSI <= X_low:
            self.RSI_is_it_below_X = False
            self.RSI_is_it_above_X = False
        elif RSI > X_high:
            self.RSI_is_it_below_X = False
            self.RSI_is_it_above_X = True
            print(f'{datetime.now()}  현재 RSI : {RSI}, {waitingTime}분간 숏 진입 대기, RSI_is_it_above_X = {self.RSI_is_it_above_X}')
            time.sleep(60*waitingTime)
        threading.Timer(3, self.update_RSI_per3s_status_thr).start()

    def update_closePrice_per1m_thr(self):
        self.close_price_1m = self.newCandleStickArr_1m[-1].close # 현재가(종가)를 불러와 전역변수에 넣어둔다.
        self.closePer1m_is_it_updated = True
        #print(f'{datetime.now()}  1분봉 종가 업데이트 {self.close_price_1m}, self.closePer1m_is_it_updated = {self.closePer1m_is_it_updated}')
        threading.Timer((60 - datetime.now().second), self.update_closePrice_per1m_thr).start() #1분마다 재귀함수 쓰레드를 반복시킨다.

    def update_ATR_position_tradeOut_signal_per1s_thr(self): #시그널은 트루만 주고 펄스주는건 따로
        if self.now_price < self.avg_15m_20 + self.avg_15m_20 * 0.01 and self.now_price > self.avg_15m_20 - self.avg_15m_20 * 0.01:
            self.ATR_tradeOut_signal = True
        threading.Timer(1, self.update_ATR_position_tradeOut_signal_per1s_thr).start()

    def what_time_is(self):
        serverTime = self.request_client.get_servertime()
        print(serverTime)
        print(datetime.today())
        print("server time: ", datetime.fromtimestamp(serverTime / 1000))
        server_obj = datetime.fromtimestamp((serverTime / 1000))
        pTime = server_obj - timedelta(days=2)
        print("one day ago : ", pTime)

    def del_signal(self, signal):
        if signal == '':
            print('이정민바보')
        if signal == 'MACD_short_signal':
            self.MACD_short_signal = False
        if signal == 'MACD_long_signal':
            self.MACD_long_signal = False
        if signal == 'MACD_tradeOut_signal':
            self.MACD_tradeOut_signal = False
        if signal == 'ATR_tradeOut_signal':
            self.ATR_tradeOut_signal = False

if __name__ == '__main__':
    a = machine()