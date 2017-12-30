# -*- coding: utf-8 -*-

import os
from datetime import datetime

import ccxt
from pymongo import MongoClient

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../env.py')
if os.path.exists(env_file):
    exec(open(env_file, 'rb').read())


def create_exchange(exchange_id):
    api_key = None
    api_secret = None
    try:
        api_key = eval('{}_KEY'.format(exchange_id.upper()))
        api_secret = eval('{}_SECRET'.format(exchange_id.upper()))
    except NameError:
        pass

    if api_key and api_secret:
        ex = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': api_secret,
        })
    else:
        ex = getattr(ccxt, exchange_id)()

    return ex


def save_ticker_to_mongo(exchange_id, currency_pair):
    """
    :param exchange_id: id of exchange market
                        ex) 'coinmarketcap', 'bittrex'
                        cf) https://github.com/ccxt/ccxt#supported-cryptocurrency-exchange-markets
    :param currency_pair: ex) 'BTC/USD'
    :return:
    """
    ex = create_exchange(exchange_id)

    # Get ticker from exchange
    ticker = ex.fetch_ticker(currency_pair)

    # Save data into MongoDB
    collection = MongoClient()['tickers'][exchange_id]
    ticker['datetime'] = datetime.fromtimestamp(ticker['timestamp'] / 1000)
    collection.insert_one(ticker)


def save_tickers_to_mongo_by_partial_currency_pair(exchange_id, partial_currency_pair):
    """
    :param exchange_id: id of exchange market
                        ex) 'coinmarketcap', 'bittrex'
                        cf) https://github.com/ccxt/ccxt#supported-cryptocurrency-exchange-markets
    :param partial_currency_pair: ex) '/JPY'
    :return:
    """
    ex = create_exchange(exchange_id)

    # Get symbols
    print(ex.fetch_markets())
    print([m['symbol'] for m in ex.fetch_markets()])
    currency_pairs = [m['symbol'] for m in ex.fetch_markets() if partial_currency_pair in m['symbol']]

    for currency_pair in currency_pairs:
        save_ticker_to_mongo(exchange_id, currency_pair)
