# -*- coding: utf-8 -*-

import os
from datetime import datetime

import requests
from pymongo import MongoClient

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../env.py')
if os.path.exists(env_file):
    exec(open(env_file, 'rb').read())


def get_fiat_rate(currency_pair):
    """
    :param currency_pair: ex) 'USD/JPY', 'EUR/JPY'
    :return:
    """
    url = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency={to_currency}&apikey={api_key}'.format(
        from_currency=currency_pair.split('/')[0],
        to_currency=currency_pair.split('/')[1],
        api_key=ALPHA_VANTAGE_API_KEY,
    )
    res_json = requests.get(url).json()
    print('res_json={}'.format(res_json))
    rate_dict = res_json['Realtime Currency Exchange Rate']
    return {
        'currency_pair': currency_pair,
        'rate': float(rate_dict['5. Exchange Rate']),
        'datetime': datetime.strptime(rate_dict['6. Last Refreshed'], '%Y-%m-%d %H:%M:%S'),
    }


def save_fiat_rate_to_mongo(currency_pair):
    """
    :param currency_pair: ex) 'USD/JPY', 'EUR/JPY'
    :return:
    """
    # Get fiat rate
    fiat_rate = get_fiat_rate(currency_pair)

    # Save data into MongoDB
    collection = MongoClient()['fiats']['alphavantage']
    collection.insert_one(fiat_rate)
