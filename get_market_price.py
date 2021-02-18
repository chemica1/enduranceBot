from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
import time
import threading

current_price = 0


def thread_run():
    global current_price
    request_client = RequestClient(api_key="cGBSO4BJK7Mmlhxnp4wUAI56wgNGZH6DrZLOzd8i1rM52EExhhgbedSxq6gqy4Sh",
                                   secret_key="")
    result = request_client.get_mark_price(symbol="BTCUSDT")
    print(result.markPrice)
    current_price = result.markPrice

    threading.Timer(0.3,thread_run).start()


thread_run()


