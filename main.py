import json
import os
import time

import pandas
import numpy as np
import argparse
from tqdm import tqdm

parser=argparse.ArgumentParser()
parser.add_argument("--symbol")
args = parser.parse_args()

# Custom Libraries
# import mt5_lib
# import ema_cross_strategy
import indicator_lib
import tradingview_lib
import yfinance_lib

# Location of settings.json
settings_filepath = "settings.json" # <- This can be modified to be your own settings filepath


# Function to import settings from settings.json
def get_project_settings(import_filepath):
    """
    Function to import settings from settings.json
    :param import_filepath: path to settings.json
    :return: settings as a dictionary object
    """
    # Test the filepath to make sure it exists
    if os.path.exists(import_filepath):
        # If yes, import the file
        f = open(import_filepath, "r")
        # Read the information
        project_settings = json.load(f)
        # Close the file
        f.close()
        # Return the project settings
        return project_settings
    # Notify user if settings.json doesn't exist
    else:
        raise ImportError("settings.json does not exist at provided location")


# Function to repeat startup proceedures
def start_up(project_settings):
    """
    Function to manage start up proceedures for App. Includes starting/testing exchanges
    initializing symbols and anything else to ensure app start is successful.
    :param project_settings: json object of the project settings
    :return: Boolean. True if app start up is successful. False if not.
    """
    # Start MetaTrader 5
    startup = mt5_lib.start_mt5(project_settings=project_settings)
    # If startup successful, let user know
    if startup:
        print("MetaTrader startup successful")
        # Initialize symbols
        # Extract symbols from project settings
        return True
    # Default return is False
    return False


# Function to run the strategy
def run_strategy(project_settings, cancel_outstanding=True):
    """
    Function to run the strategy for the trading bot
    :param project_settings: JSON of project settings
    :return: Boolean. Strategy ran successfully with no errors=True. Else False.
    """
    # Extract the symbols to be traded
    symbols = project_settings["mt5"]["symbols"]
    # Extract the timeframe to be traded
    timeframe = project_settings["mt5"]["timeframe"]
    # Strategy Risk Management
    # Get a list of open orders
    orders = mt5_lib.get_all_open_orders()
    # Iterate through the open orders and cancel
    # TODO: Does this cancel currently bought or sold positions?
    if cancel_outstanding:
        for order in orders:
            mt5_lib.cancel_order(order)
    # Run through the strategy of the specified symbols
    for symbol in symbols:
        # Strategy Risk Management
        # Generate the comment string
        comment_string = project_settings['mt5']['strategy_name'] + "_{symbol}"
        # Cancel any open orders related to the symbol and strategy
        if cancel_outstanding:
            mt5_lib.cancel_filtered_orders(
                symbol=symbol,
                comment=comment_string
            )
        # Trade Strategy
        data = getattr(eval(project_settings["mt5"]["strategy_name"]), project_settings["mt5"]["strategy_name"])(
            symbol=symbol,
            timeframe=timeframe,
            strategy_settings=project_settings['mt5']['strategy_settings']
        )
        if data:
            print(f"Trade Made on {symbol}")
        else:
            print(f"No trade for {symbol}")
    # Return True. Previous code will throw a breaking error if anything goes wrong.
    return True

def get_time(timeframe):
    time_candle = mt5_lib.get_candlesticks(
        symbol="EURUSD",
        timeframe=timeframe,
        number_of_candles=1
    )
    if len(time_candle) < 1:
        raise Exception(f"Retrieving current time failed.")
    # Extract the time
    current_time = time_candle['time'][0]
    return current_time

# Main function
if __name__ == '__main__':
    print("Let's build an awesome trading bot!!!")
    # Import settings.json
    project_settings = get_project_settings(import_filepath=settings_filepath)
    # Run through startup proceedure
    # startup = start_up(project_settings=project_settings)
    # Make it so that all columns are shown
    pandas.set_option('display.max_columns', None)

    dte = 50

    if args.symbol:
        symbols_to_observe = [args.symbol]
    else:
        # symbols_to_observe = tradingview_lib.get_most_active()['name']
        symbols_to_observe = tradingview_lib.get_most_volume(limit=500)['name']
        # symbols_to_observe = tradingview_lib.get_most_obv()['name']

    symbols_with_low_rsi = {}
    symbols_with_good_obv = {}
    symbols_with_good_deltas = {}

    # for symbol in tqdm(symbols_to_observe):
    #     ticker_data = yfinance_lib.get_ticker_data(symbol)
    #     obv = (np.sign(ticker_data['Close'].diff())*ticker_data['Volume']).fillna(0).cumsum()[-4:]
    #     if len(obv) > 3 and obv.iloc[3] > obv.iloc[2] and obv.iloc[2] > obv.iloc[1] and obv.iloc[1] > obv.iloc[0]:
    #         symbols_with_good_obv[symbol] = obv

    # print(f'Symbols with good on-balance volume: {symbols_with_good_obv}')
    tickers = {symbol: yfinance_lib.get_ticker(symbol) for symbol in symbols_to_observe}

    for symbol in tqdm(symbols_to_observe):
        ticker = tickers[symbol]
        ticker_data = yfinance_lib.get_data(ticker)
        rsi = indicator_lib.calc_rsi(ticker_data)[-4:]        
        if len(rsi) > 0 and (rsi.iloc[0] < 35 or rsi.iloc[1] < 35):
            symbols_with_low_rsi[symbol] = rsi
    
    print(f'Symbols with low rsi: {symbols_with_low_rsi}')
    


    for symbol in tqdm(symbols_with_low_rsi):
        ticker = tickers[symbol]
        current_price = yfinance_lib.get_current_price(symbol)
        deltas = yfinance_lib.get_delta_values(ticker, dte, current_price)
        if deltas is None or len(deltas['strike']) < 5:
            continue
        indices_near_current_price = deltas.iloc[(deltas['strike']-current_price).abs().argsort()[:5]].index.tolist()
        for i in indices_near_current_price:
            if deltas.iloc[i]['difference'] < 0:
                break
            else:
                if i == indices_near_current_price[len(indices_near_current_price)-1]:
                    symbols_with_good_deltas[symbol] = deltas
    
    print('Symbols with low rsi:' )
    for symobls in symbols_with_good_deltas:
        print(symbol, ':', symbols_with_low_rsi[symbol])
    print(f'Symbols with good deltas too:\n{symbols_with_good_deltas}')
    print(f'Recommended: {list(symbols_with_good_deltas.keys())}')


        

    if False == True:
        if len(project_settings['mt5']['symbols']) == 0:
            project_settings["mt5"]["symbols"] = symbols = mt5_lib.get_all_mt5_symbols()
        symbols = project_settings["mt5"]["symbols"]
        # Iterate through the symbols to enable
        for symbol in symbols:
            outcome = mt5_lib.initialize_symbol(symbol)
            # Update the user
            if outcome is True:
                print(f"Symbol {symbol} initalized")
            else:
                raise Exception(f"{symbol} not initialized")
        # Set a variable for the current time
        current_time = 0
        # Set a variable for previous time
        previous_time = 0
        # Specify the startup timeframe
        timeframe = project_settings["mt5"]["timeframe"]
        # Start while loop
        while 1:
            # Update trailing stops for any positions
            mt5_lib.update_trailing_stops(10)
            # Get a value for current time. Use BTCUSD as it trades 24/7
            current_time = get_time(timeframe)
            # Compare the current time against the previous time.
            if current_time != previous_time:
                # This means that a new candle has occurred. Proceed with strategy
                print("New Candle! Let's trade.")
                # Update previous time so that it is given the new current_time
                previous_time = current_time
                # Run the strategy
                strategy = run_strategy(project_settings=project_settings)
                #print(strategy)

            else:
                # No new candle has occurred
                time.sleep(1)