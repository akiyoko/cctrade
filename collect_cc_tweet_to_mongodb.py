# -*- coding: utf-8 -*-

import logging
import os

import requests
import tweepy
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

NUMBER_OF_COINS = 200


class MyListener(tweepy.StreamListener):
    def __init__(self):
        super(MyListener, self).__init__()
        self.collection_hashtags = MongoClient().cctweet['hashtags']
        self.collection_symbols = MongoClient().cctweet['symbols']

    def on_status(self, status):
        print('------------------------------')
        print(status.text)
        # Ignore spams
        # TODO: threshold is 5, enough?
        if len(status.entities['hashtags']) > 5 or len(status.entities['symbols']) > 5:
            return True

        # Symbols
        for symbol in status.entities['symbols']:
            print(symbol)
            self.collection_symbols.update_one(
                {'key': symbol['text'].lower(), 'time': {'$exists': False}},
                {'$inc': {'count': 1}},
                upsert=True)
        # Hashtags
        for hashtag in status.entities['hashtags']:
            print(hashtag)
            self.collection_hashtags.update_one(
                {'key': hashtag['text'].lower(), 'time': {'$exists': False}},
                {'$inc': {'count': 1}},
                upsert=True)

    def on_error(self, status_code):
        print('Got an error with status code: {}'.format(status_code))
        logger.error('Got an error with status code: {}'.format(status_code))
        if status_code == 420:
            return False

    # See: https://stackoverflow.com/questions/14177327/tweepy-stops-after-a-few-hours
    def on_disconnect(self, notice):
        print('Got a disconnect signal with notice: {}'.format(notice))
        logger.error('Got a disconnect signal with notice: {}'.format(notice))
        return False


@retry(wait_random_min=3000, wait_random_max=5000)
def main():
    # Use CoinMarketCap JSON API
    # Details at https://coinmarketcap.com/api/
    try:
        res = requests.get('https://api.coinmarketcap.com/v1/ticker/')
        resj = res.json()
        print('Size of Symbols={}'.format(len(resj)))
        symbols = [d['symbol'] for d in resj]
        print('Symbols={}'.format(symbols))
    except Exception as e:
        print('Got an error: {}'.format(str(e)))
        logger.error('Got an error: {}'.format(str(e)))
        raise

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    listener = MyListener()
    stream = tweepy.Stream(auth=auth, listener=listener, retry_count=20)
    keywords = ['bitcoin', 'blockchain', 'cryptocurrency', 'crypto', 'altcoin', '#ico']
    # Add top hundreds of coins to keywords
    keywords.extend(['${}'.format(symbol.lower()) for symbol in symbols[:NUMBER_OF_COINS]])
    print('keywords={}'.format(keywords))
    # Do not add 'async' option for retry
    stream.filter(track=keywords)  # , async=True)


if __name__ == "__main__":
    main()
