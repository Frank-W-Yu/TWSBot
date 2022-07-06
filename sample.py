#!/usr/bin/env python3


from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import TickerId, BarData, OrderId
from ibapi.contract import Contract, ContractDetails
from ibapi.order import Order
from threading import Thread, Event
from time import sleep
from flask import Flask, request
import pandas as pd
from waitress import serve
import json
from typing import Optional
from sqlalchemy import create_engine

web_app = Flask(__name__)


class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}
        self.nextValidOrderId = 0

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        print(f"Error: {reqId}, {errorCode}, {errorString}")

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        print(f"ReqId: {reqId}, contract details: {contractDetails}.")
        # return super().contractDetails(reqId, contractDetails)

    def serialize_bar_data(self, bar: BarData) -> str:
        return json.dumps({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'bar_count': bar.barCount,
            'average': bar.average,
        })

    def historicalData(self, reqId: int, bar: BarData):
        # if reqId not in self.data:
        #     self.data[reqId] = []
        self.data[reqId] = self.serialize_bar_data(bar)
        # print("HistoricalData. ReqId:", reqId, "BarData.", bar)
        # return bar

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        print(reqId, account, tag, value, currency)

    def positionMulti(self, reqId: int, account: str, modelCode: str, contract: Contract, pos: float, avgCost: float):
        print(reqId, account, modelCode, contract, pos, avgCost)

    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        print(account, contract, position, avgCost)

    def placeOrder(self, orderId: OrderId, contract: Contract, order: Order):
        return super().placeOrder(orderId, contract, order)

    def get_next_valid_order_id(self) -> int:
        self.nextValidOrderId += 1
        return self.nextValidOrderId


def websocket_con():
    app.run()
    # event.wait()
    # if event.is_set():
    #     app.disconnect()


def reader():
    while app.isConnected():
        if len(app.data) > 0:
            print("Get data!")
            print(app.data.pop())
        sleep(0.1)


def create_stk_contract(symbol: str,
                        sec_type: str = "STK",
                        currency: str = "USD",
                        exchange: str = "SMART"
                        ) -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract


def create_order(action: str, quantity: int,  order_type: str = "LMT", limit_price: Optional[float] = None, ) -> Order:
    order = Order()
    order.action = action
    order.orderType = order_type
    order.totalQuantity = quantity
    if limit_price:
        order.lmtPrice = limit_price
    return order


@web_app.route('/historical_data', methods=['POST'])
def post_get_historical_data():
    body_json = request.get_data().decode('utf-8')
    body_dict = json.loads(body_json)
    symbol = body_dict['symbol']
    contract = create_stk_contract(symbol)
    return get_historical_data(10, contract, duration='3 D')


@web_app.route('/place_order', methods=["POST"])
def place_order():
    body_json = request.get_data().decode('utf-8')
    body_dict = json.loads(body_json)
    symbol = body_dict['symbol']
    action = body_dict['action']
    limit_price = body_dict['limit_price']
    quantity = body_dict['quantity']
    contract = create_stk_contract(symbol)
    order = create_order(action=action, quantity=quantity,
                         limit_price=limit_price)
    order_id = app.get_next_valid_order_id()
    app.placeOrder(orderId=order_id, contract=contract, order=order)
    return {'order_id': order_id}


def get_historical_data(req_num: int,
                        contract: Contract,
                        end_data_time: str = '',
                        duration: str = '3 M',
                        bar_size: str = '1 day',
                        what_to_show: str = "ADJUSTED_LAST",
                        use_rth: int = 1,
                        format_date: int = 1,
                        keep_up_to_date: int = 0,
                        chart_options=[]) -> None:
    app.reqHistoricalData(reqId=req_num,
                          contract=contract,
                          endDateTime=end_data_time,
                          durationStr=duration,
                          barSizeSetting=bar_size,
                          whatToShow=what_to_show,
                          useRTH=use_rth,
                          formatDate=format_date,
                          keepUpToDate=keep_up_to_date,
                          chartOptions=chart_options,
                          )
    while True:
        if req_num in app.data:
            return app.data.pop(req_num)
        sleep(1)


event = Event()
app = TestApp()
app.connect("192.168.50.44", 7496, clientId=1)
# app.run()

con_thread = Thread(target=websocket_con, daemon=True)
con_thread.start()
sleep(1)

serve(web_app, host='0.0.0.0', port=8002)
# reader_thread = Thread(target=reader, daemon=True)
# reader_thread.start()

# app.reqAccountSummary(reqId=10, groupName='All', tags=[])
# app.reqPositions()
# for i, symbol in enumerate(['AAPL', 'AMZN', 'TSLA']):
#     contract = create_stk_contract(symbol)
#     get_historical_data(i, contract, duration='3 D')

# con_thread.join()
# sleep(5)
# print(app.data)
# event.set()
# sys.exit()
