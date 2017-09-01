# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime, timedelta
from pprint import pprint

import ccxt
from pymongo import MongoClient

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'env.py')
if os.path.exists(env_file):
    exec(open(env_file, 'rb').read())

logging.basicConfig(
    level=logging.DEBUG,
    filename='cctrade.log',
    format='%(asctime)s %(levelname)-7s %(message)s',
)
logger = logging.getLogger(__name__)


def main():
    now = datetime.now()

    # Get markets
    exchange = ccxt.bittrex()
    markets = exchange.fetch_tickers()
    print('Number of markets={}'.format(len(markets)))
    # Bitcoin
    bitcoin = dict(markets.pop('BTC/USDT'), symbol='BTC')
    pprint(bitcoin)
    # Altcoins
    altcoins = [dict(v, symbol=k.split('/')[0]) for k, v in markets.items() if '/BTC' in k]
    # Sort by baseVolume (Note: baseVolume might be None, so 'or 0')
    altcoins.sort(key=lambda x: float(x['baseVolume'] or 0), reverse=True)
    pprint(altcoins)
    print('Number of altcoins={}'.format(len(altcoins)))
    print([x['symbol'] for x in altcoins])

    # Save coin data to MongoDB
    collection = MongoClient().bittrex['tickers']
    # TODO: [bitcoin] + altcoins[:100], if you want save bitcoin and top 100 altcoins
    for coin in [bitcoin] + altcoins:
        coin['timestamp'] = datetime.fromtimestamp(coin['timestamp'] / 1000)
        collection.insert_one(coin)

    # Cleanup
    collection.remove({'last_updated': {'$lt': now - timedelta(hours=24 * 10)}})


if __name__ == "__main__":
    main()
