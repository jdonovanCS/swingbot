import yfinance as yf
import os
import json
import time
import pandas_datareader.data as web
import pandas as pd
import math

import datetime
import numpy as np
from scipy.stats import norm
import argparse


parser=argparse.ArgumentParser()
parser.add_argument("--symbol")
args = parser.parse_args()

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



def calculate_delta(option_type, S, K, T, r, sigma):
    d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    if option_type == 'call':
        return norm.cdf(d1)
    elif option_type == 'put':
        return norm.cdf(d1) - 1


project_settings = get_project_settings(import_filepath=settings_filepath)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def get_delta_values(ticker, dte):

    yf_ticker = yf.Ticker(ticker)
    # print(f'Retrieving options for {ticker}:\nyf_ticker.options')
    
    risk_free_rate = web.DataReader('SOFR', 'fred', datetime.datetime.today()-datetime.timedelta(days=5), datetime.datetime.today())['SOFR'].iloc[-1]
    # print(f'Retrieving risk-free interest rate: {risk_free_rate}')

    current_price = get_current_price(ticker)

    count = 0
    while count < len(yf_ticker.options) and datetime.datetime.strptime(yf_ticker.options[count], "%Y-%m-%d").date() - datetime.date.today() < datetime.timedelta(dte):
        if (datetime.datetime.strptime(yf_ticker.options[count], "%Y-%m-%d") - pd.Timestamp.today()).days < 1:
            count+=1
            continue
        calls = pd.DataFrame(yf_ticker.option_chain(date=yf_ticker.options[count]).calls).sort_values(by=['strike'], ascending=False)
        calls = calls[(calls['strike'] > current_price - current_price*.30) & (calls['strike'] < current_price + current_price*.30)]
        calls['delta'] = calls.apply(lambda row: calculate_delta('call', current_price, row['strike'], 
                                                        ((datetime.datetime.strptime(yf_ticker.options[count], "%Y-%m-%d") - pd.Timestamp.today()).days / 365), 
                                                        risk_free_rate/100, row['impliedVolatility']), axis=1)
        calls['delta_dollars'] = (calls['delta'])*calls['openInterest']*10

        puts = pd.DataFrame(yf_ticker.option_chain(date=yf_ticker.options[count]).puts).sort_values(by=['strike'], ascending=False)
        puts = puts[(puts['strike'] > current_price - current_price*.30) & (puts['strike'] < current_price + current_price*.30)]
        puts['delta'] = puts.apply(lambda row: calculate_delta('put', current_price, row['strike'], 
                                                        ((datetime.datetime.strptime(yf_ticker.options[count], "%Y-%m-%d") - pd.Timestamp.today()).days / 365), 
                                                        risk_free_rate/100, row['impliedVolatility']), axis=1)
        puts['delta_dollars'] = (puts['delta'])*puts['openInterest']*-1*10

        if 'total_calls' not in locals():
            total_calls = pd.DataFrame(calls[['delta_dollars', 'strike']])
            total_calls['total_dollars'] = total_calls['delta_dollars']
            total_calls = total_calls[['strike', 'total_dollars']]
            total_puts = pd.DataFrame(puts[['delta_dollars', 'strike']])
            total_puts['total_dollars'] = total_puts['delta_dollars']
            total_puts = total_puts[['strike', 'total_dollars']]

        else:
            total_calls = total_calls.merge(pd.DataFrame(calls[['delta_dollars', 'strike']]), left_on='strike', right_on='strike', how='outer')
            total_calls['total_dollars'] = total_calls['total_dollars'].fillna(0)
            total_calls['delta_dollars'] = total_calls['delta_dollars'].fillna(0)
            total_calls['total_dollars'] = total_calls['delta_dollars'] + total_calls['total_dollars']
            total_calls = total_calls[['strike', 'total_dollars']]
            total_puts = total_puts.merge(pd.DataFrame(puts[['delta_dollars', 'strike']]), left_on='strike', right_on='strike', how='outer')
            total_puts['total_dollars'] = total_puts['total_dollars'].fillna(0)
            total_puts['delta_dollars'] = total_puts['delta_dollars'].fillna(0)
            total_puts['total_dollars'] = total_puts['delta_dollars'] + total_puts['total_dollars']
            total_puts = total_puts[['strike', 'total_dollars']]
        count+=1

    # print(total_calls)
    # print(total_puts)
    if 'total_calls' in locals():
        combined = total_calls.merge(total_puts, right_on='strike', left_on='strike', how='outer', suffixes=('_calls', '_puts'))
        combined['total_dollars_calls'] = combined['total_dollars_calls'].fillna(0)
        combined['total_dollars_puts'] = combined['total_dollars_puts'].fillna(0)
        combined['difference'] = combined['total_dollars_calls'] - combined['total_dollars_puts']
        combined = combined.sort_values(by=['strike'], ascending=False)
    # print(combined)

        return combined
    return None


def get_ticker_data(ticker):
    yf_ticker = yf.Ticker(ticker)
    return yf_ticker.history(period="1mo")

def get_current_price(ticker):
    yf_ticker = yf.Ticker(ticker)
    if hasattr(yf_ticker.info, 'currentPrice'):
        current_price = yf_ticker.info['currentPrice']
    else:
        current_price=yf_ticker.history()['Close'].iloc[-1]
    return current_price


if args.symbol:
    print(get_delta_values(args.symbol, 350))





# # only gets calls expiring this day.
# options_chain = yf_ticker.option_chain(date='2024-12-20')

# # print(pd.DataFrame(options_chain.calls)[['volume', 'strike']])

# # options_chain = yf_ticker.option_chain(date=dte_50)

# # print(pd.DataFrame(options_chain.calls)[['volume', 'strike']])


# sofr_data = web.DataReader('SOFR', 'fred', datetime.datetime.today()-datetime.timedelta(days=2), datetime.datetime.today())
# # print(sofr_data.tail())
# risk_free_rate = sofr_data['SOFR'][-1]
# print(f'Risk Free Rate: {risk_free_rate}')


# calls = pd.DataFrame(options_chain.calls).sort_values(by=['strike'])



# puts  = pd.DataFrame(options_chain.puts).sort_values(by=['strike'])


# current_price = yf_ticker.info['currentPrice']
# print(f"Current price: {current_price}")

# print(calls.columns)

# calls = calls[(calls['strike'] > current_price - current_price*.20) & (calls['strike'] < current_price + current_price*.20)]
# puts = puts[(puts['strike'] > current_price - current_price*.20) & (puts['strike'] < current_price + current_price*.20)]


# # I think I'm doing time to expiry correctly now.. see keep for original ai-generated code.
# calls['delta'] = calls.apply(lambda row: calculate_delta('call', current_price, row['strike'], 
#                                                         ((datetime.datetime.strptime('2024-12-20', "%Y-%m-%d") - pd.Timestamp.today()).days / 365), 
#                                                         risk_free_rate/100, row['impliedVolatility']), axis=1)


# puts['delta'] = puts.apply(lambda row: calculate_delta('put', current_price, row['strike'], 
#                                                         ((datetime.datetime.strptime('2024-12-20', "%Y-%m-%d") - pd.Timestamp.today()).days / 365), 
#                                                         risk_free_rate/100, row['impliedVolatility']), axis=1)



# calls['volume'] = calls['volume'].fillna(0)
# puts['volume'] = puts['volume'].fillna(0)

# calls['delta_dollars'] = (calls['delta'])*calls['openInterest']*10
# puts['delta_dollars'] = (puts['delta'])*puts['openInterest']*-1*10

# print(calls[['strike', 'lastPrice', 'volume', 'openInterest', 'delta', 'delta_dollars']])
# print(puts[['strike', 'lastPrice', 'volume', 'openInterest', 'delta', 'delta_dollars']])