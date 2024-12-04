from tradingview_screener import Scanner, Query, Column
import pandas as pd

def get_most_active():

    nrows, ret = Scanner.premarket_most_active.get_scanner_data()
    return ret

def get_most_volume(limit=100):
    nrows, ret = Query().select('name', 'close', 'volume').order_by('volume', ascending=False).limit(limit).get_scanner_data()
    return ret

def get_most_volume_with_low_rsi(limit=100):
    nrows, ret = (Query().select('name', 'close', 'volume')
                        .where
                            (Column('RSI')<=35).order_by('volume', ascending=False).limit(limit=limit)).get_scanner_data()
    return ret

def get_testing_queries(limit=100):
    nrows, ret = (Query().select('name', 'close', 'volume')
                        .where
                            (Column('RSI')<=35).order_by('volume', ascending=False).limit(limit=limit)).get_scanner_data()
    print(ret)
    return ret