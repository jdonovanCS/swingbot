from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        print('The next valid order id is: ', orderId)

def main():
    app = IBapi()
    app.connect('127.0.0.1', 7497, 1)

    contract = Contract()
    contract.symbol = 'ALAB'
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'

    app.reqMktData(1, contract, '', False, False, [])

    app.run()

if __name__ == "__main__":
    main()