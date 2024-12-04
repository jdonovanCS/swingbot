import numpy as np
import talib


def calc_custom_ema_talib(dataframe, ema_size):
    ema_name = "ema_" + str(ema_size)
    dataframe[ema_name] = talib.EMA(dataframe['close'], timeperiod=ema_size)
    return dataframe

# Define a function to calculate a custom EMA of any size
def calc_custom_ema(dataframe, ema_size):
    """
    Function to calculate a dataframe of any size. Does not use TA-Lib, so is a custom implementation.
    Recommended to keep dataframe size < 1000 rows to preserve speed.
    :param dataframe: dataframe object of the price data to apply ema to
    :param ema_size: integer of the size of EMA
    :return: dataframe with EMA attached
    """
    # Create the name of the column to be added
    ema_name = "ema_" + str(ema_size)
    # Create the multiplier
    multiplier = 2 / (ema_size + 1)
    # Calculate the initial value. This will be a Simple Moving Average
    initial_mean = dataframe['close'].head(ema_size).mean()
    # Iterate through the dataframe and add the values
    for i in range(len(dataframe)):
        # If i is the size of the EMA, value is the initial mean
        if i == ema_size:
            dataframe.loc[i, ema_name] = initial_mean
        # If i is > ema_size, calculate the EMA
        elif i > ema_size:
            ema_value = dataframe.loc[i, 'close'] * multiplier + dataframe.loc[i-1, ema_name]*(1-multiplier)
            dataframe.loc[i, ema_name] = ema_value
        # If i is < ema_size (also the default condition)
        else:
            dataframe.loc[i, ema_name] = 0.00

    # Once completed, return the completed dataframe to the user
    return dataframe


# Function to calculate a crossover event between two EMAs
def ema_cross_calculator(dataframe, ema_one, ema_two):
    """
    Function to calculate an EMA cross event. EMA Column names must be in the format ema_<value>. I.e. an EMA 200
    would be ema_200
    :param dataframe: dataframe object
    :param ema_one: integer of EMA 1 size
    :param ema_two: integer of EMA 2 size
    :return: dataframe with cross events
    """
    # Get the column names
    ema_one_column = "ema_" + str(ema_one)
    ema_two_column = "ema_" + str(ema_two)
    # Create a position column
    dataframe['position'] = dataframe[ema_one_column] > dataframe[ema_two_column]
    # Create a pre-position column
    dataframe['pre_position'] = dataframe['position'].shift(1)
    # Drop any NA values
    dataframe.dropna(inplace=True)
    # Define the Crossover events
    dataframe['ema_cross'] = np.where(dataframe['position'] == dataframe['pre_position'], False, True)
    # Drop the position and pre_position columns
    dataframe = dataframe.drop(columns="position")
    dataframe = dataframe.drop(columns="pre_position")
    # Return dataframe
    return dataframe

def calc_rsi(data, window=14):
    """Calculates the RSI for a given DataFrame and window."""

    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)

    # Calculate the exponential moving averages for up and down moves
    ema_up = up.ewm(com=window - 1, adjust=False).mean()
    ema_down = down.ewm(com=window - 1, adjust=False).mean()

    # Calculate the relative strength (RS)
    rs = ema_up / ema_down

    # Calculate the RSI
    rsi = 100 - (100 / (1 + rs))

    return rsi

def calc_trend_over_time(data, windows=[1,30,60,90,180,365]):
    trend = 0
    
    for window in windows:
        for window2 in windows:
            if window2 <= window:
                continue
            if len(data['Close'])>= window and len(data['Close']) >= window2 and data['Close'].iloc[-1*window2] <= data['Close'].iloc[-1*window]:
                trend += 1
            else:
                trend -= 1
    return trend


