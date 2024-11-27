from tradingview_screener import Scanner, Query, Column
import pandas as pd

def get_most_active():

    nrows, ret = Scanner.premarket_most_active.get_scanner_data()
    return ret

def get_most_volume():
    nrows, ret = Query().select('name', 'close', 'volume', 'relative_volume_10d_calc').order_by('volume', ascending=False).limit(1000).get_scanner_data()
    return ret

def get_most_obv():
    nrows, ret = Query().select('name', 'close', 'volume', 'relative_volume_10d_calc').where(Column('on_balance_volume').between(100_000_000, 1_000_000_000)).order_by('volume', ascending=False)

