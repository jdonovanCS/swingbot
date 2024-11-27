import mt5_lib
import indicator_lib
import make_trade
import numpy as np


# Function to run the EMA Cross Strategy
def ema_cross_strategy(symbol, timeframe, strategy_settings):
    """
    Function which runs the EMA Cross Strategy
    :param symbol: string of the symbol to be queried
    :param timeframe: string of the timeframe to be queried
    :param strategy_settings: For this strategy their are 4:
        ema_one: integer of the lowest timeframe length for EMA
        ema_two: integer of the highest timeframe length for EMA
        balance: 
        amount_to_risk:
    :return: trade event dataframe
    """
    #### Pseudo Code Steps
    # Step 1: Retrieve data -> get_data()
    # Step 2: Calculate indicators - calc_indicators()
    # Step 3: Determine if a trade event has occurred - det_trade()
    # Step 4: Check previous trade
    # Step 5: If trade event has occurred, send order

    # Step 1: Retrieve data
    data = get_data(
        symbol=symbol,
        timeframe=timeframe
    )
    # Step 2: Calculate indicators
    data = calc_indicators(
        data=data,
        ema_one=strategy_settings['ema_one'],
        ema_two=strategy_settings['ema_two']
    )
    # Step 3: Determine if a trade event has occurred
    data_trade = det_trade(
        data=data,
        ema_one=strategy_settings['ema_one'],
        ema_two=strategy_settings['ema_two']
    )
    # Step 4: Check last line of dataframe
    trade_event = data_trade.tail(1).copy()
    # See if 'ema_cross' is true
    if trade_event['ema_cross'].values:
        
        # Make Trade requires balance, comment, amount_to_risk
        # Create comment
        comment_string = f"EMA_Cross_strategy_{symbol}"
        print(comment_string)
        # TODO: Cancel any positions with regard to this symbol
        pos_type=None
        if trade_event['stop_price'].values > trade_event['stop_loss'].values:
            pos_type = "BUY"
        elif trade_event['stop_price'].values < trade_event['stop_loss'].values:
            pos_type = "SELL"
        mt5_lib.close_filtered_positions(symbol=symbol, pos_type=pos_type, comment=comment_string)
        # Make Trade
        make_trade_outcome = make_trade.make_trade(
            balance=strategy_settings['balance'],
            comment=comment_string,
            amount_to_risk=strategy_settings['amount_to_risk'],
            symbol=symbol,
            take_profit=trade_event['take_profit'].values,
            stop_price=trade_event['stop_price'].values,
            stop_loss=trade_event['stop_loss'].values,
            stop=strategy_settings['stop']
        )

    else:
        make_trade_outcome = False
    print(f'EMA: {make_trade_outcome}')
    return make_trade_outcome


# Function to determine if a trade event has occurred, and if so, calculate trade signal
def det_trade(data, ema_one, ema_two):
    """
    Function to calculate a trade signal for the strategy. For the EMA Cross Strategy, rules are as follows:
    1. For each trade, stop_loss is the corresponding highest EMA (i.e. if ema_one is 50 and ema_two is 200, stop_loss
    is ema_200)
    2. For a BUY (GREEN Candle), the entry price (stop_price) is the high of the previous completed candle
    3. For a SELL (RED Candle), the entry price (stop_price) is the low of the previous completed candle
    4. The take_profit is the absolute distance between the stop_price and stop_loss, added to a BUY stop_price and
    subtracted from a SELL stop_price
    :param dataframe: dataframe of data with indicators
    :param ema_one: integer of EMA size
    :param ema_two: integer of EMA size
    :return: dataframe with trade values added
    """
    # Get the EMA Column names
    ema_one_column = "ema_" + str(ema_one)
    ema_two_column = "ema_" + str(ema_two)
    # Choose the largest EMA (i.e. the EMA which will be used for the Stop Loss
    if ema_one > ema_two:
        ema_column = ema_one_column
        min_value = ema_one
    elif ema_two > ema_one:
        ema_column = ema_two_column
        min_value = ema_two
    else:
        # EMA values are equal, so raise an error
        raise ValueError("EMA values are the same!")
    # Copy the dataframe to avoid copy warnings
    dataframe = data.copy()

    # Add take profit, stop loss and stop price columns to the dataframe
    dataframe['take_profit'] = 0.00
    dataframe['stop_price'] = 0.00
    dataframe['stop_loss'] = 0.00

    # Set values for stop_price, stop_loss, take_profit where ema_cross is true and in buying position, otherwise set to selling position
    dataframe['stop_price'] = np.where((dataframe['ema_cross'] == True) & (dataframe['open']<dataframe['close']), dataframe['high'], dataframe['low'])
    dataframe['stop_loss'] = np.where((dataframe['ema_cross'] == True) & (dataframe['open']<dataframe['close']), dataframe[ema_column], dataframe[ema_column])
    dataframe['take_profit'] = np.where((dataframe['ema_cross'] == True) & (dataframe['open']<dataframe['close']), dataframe['stop_price']+(dataframe['stop_price']-dataframe['stop_loss']), dataframe['stop_price']-(dataframe['stop_loss']-dataframe['stop_price']))

    # Reset values where ema_cross is not true since the last statements assume it is either buying or selling
    dataframe['stop_price'] = np.where(dataframe['ema_cross']==False, 0.00, dataframe['stop_price'])
    dataframe['stop_loss'] = np.where(dataframe['ema_cross']==False, 0.00, dataframe['stop_loss'])
    dataframe['take_profit'] = np.where(dataframe['ema_cross']==False, 0.00, dataframe['take_profit'])

    # Return the dataframe
    return dataframe


# Function to calculate the indicators for this strategy
def calc_indicators(data, ema_one, ema_two):
    """
    Function to calculate the indicators for the EMA Cross strategy
    :param data: dataframe of the raw data
    :param ema_one: integer for the first ema
    :param ema_two: integer for the second ema
    :return: dataframe with updated columns
    """
    # Calculate the first EMA
    dataframe = indicator_lib.calc_custom_ema_talib(
        dataframe=data,
        ema_size=ema_one
    )
    # Calculate the second EMA
    dataframe = indicator_lib.calc_custom_ema_talib(
        dataframe=dataframe,
        ema_size=ema_two
    )
    # Calculate the EMA Cross
    dataframe = indicator_lib.ema_cross_calculator(
        dataframe=dataframe,
        ema_one=ema_one,
        ema_two=ema_two
    )
    # Return the dataframe with all indicators
    return dataframe


# Function to retrieve data for strategy
def get_data(symbol, timeframe):
    """
    Function to retrieve data from MT5. Data is in the form of candlesticks and is retrieved as a dataframe
    :param symbol: string of the symbol to be retrieved
    :param timeframe: string of the timeframe to be retrieved
    :return: dataframe of data
    """
    # Retreive data
    data = mt5_lib.get_candlesticks(
        symbol=symbol,
        timeframe=timeframe,
        number_of_candles=1000
    )
    # Return data
    return data