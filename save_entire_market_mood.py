# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime
from pprint import pprint

import requests
from pymongo import MongoClient
from retrying import retry

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'env.py')
if os.path.exists(env_file):
    exec(open(env_file, 'rb').read())
logging.basicConfig(
    level=logging.DEBUG,
    filename='cctrade.log',
    format='%(asctime)s %(levelname)-7s %(message)s',
)
logger = logging.getLogger(__name__)

NUMBER_OF_SYMBOLS = 200


@retry(wait_random_min=3000, wait_random_max=5000)
def main():
    # Get all markets
    res = requests.get('https://api.coinmarketcap.com/v1/ticker/')
    markets = res.json()
    print('Number of markets={}'.format(len(markets)))

    # Sort by 24h_volume_usd (Note: some 24h_volume_usd are None, so 'or 0')
    markets.sort(key=lambda x: float(x['24h_volume_usd'] or 0), reverse=True)
    pprint(markets)

    collection = MongoClient().coinmarketcap['tickers']

    for market in markets[:NUMBER_OF_SYMBOLS]:
        market['last_updated'] = datetime.fromtimestamp(int(market['last_updated']))
        collection.update(
            {'symbol': market['symbol'], 'last_updated': market['last_updated']},
            market,
            upsert=True
        )


if __name__ == "__main__":
    main()
