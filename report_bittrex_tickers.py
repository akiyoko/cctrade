# -*- coding: utf-8 -*-

import logging
import os
import textwrap
from datetime import datetime, timedelta
from pprint import pprint

import ccxt
import pandas as pd
from pymongo import MongoClient, ASCENDING

from email_client import EmailClient

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'env.py')
if os.path.exists(env_file):
    exec(open(env_file, 'rb').read())

logging.basicConfig(
    level=logging.DEBUG,
    filename='cctrade.log',
    format='%(asctime)s %(levelname)-7s %(message)s',
)
logger = logging.getLogger(__name__)

# https://stackoverflow.com/a/11711637/8426544
pd.set_option('display.max_rows', 20)
pd.set_option('display.width', 1000)

DISPLAY_NUMBER_OF_ALTCOINS = 50  # TODO
TARGET_MINUTES = 10 * 24 * 60  # TODO
COMPARE_TICKS = 5
MINUTES_PER_TICK = 5  # Interval time between tickers (DO NOT CHANGE)
ROLLING_WINDOW = 50  # (DO NOT CHANGE)


def tickers_to_chart_dict(tickers):
    df = pd.DataFrame(tickers)
    df['timestamp'] = df['timestamp'].astype(datetime)
    print("size of df={}".format(len(df)))

    df['price_diff'] = df['last'] - df['last'].shift(1)
    df['price_diff_rate'] = df['price_diff'] / df['last'].shift(1)
    df['rolling_mean'] = df['last'].rolling(window=ROLLING_WINDOW).mean()
    df['rolling_std'] = df['last'].rolling(window=ROLLING_WINDOW).std()
    df['price_diff_by_sigma'] = (df['last'] - df['rolling_mean']) / df['rolling_std']
    df['volume_diff'] = df['baseVolume'] - df['baseVolume'].shift(1)
    df['volume_diff_rate'] = df['volume_diff'] / df['baseVolume'].shift(1)
    print(df)

    highest_idx = df['high'].idxmax()
    highest_price = df.loc[highest_idx]['high']
    highest_timestamp = df.loc[highest_idx]['timestamp']

    df_latest = df.tail(1)
    latest_price = df_latest['last'].values[0]
    latest_timestamp = df_latest['timestamp'].values[0]
    highest_timestamp_diff = latest_timestamp - highest_timestamp
    sigma_percent = df_latest['rolling_std'].values[0] / latest_price

    df_tails = df.tail(COMPARE_TICKS)
    price_up_downs = df_tails['price_diff_rate'].values
    volume_up_downs = df_tails['volume_diff_rate'].values
    price_diff_by_sigma = df_tails['price_diff_by_sigma'].values

    del df
    del df_latest
    del df_tails
    del tickers
    pprint(dict(locals()))
    return dict(locals())


def main():
    now = datetime.now()

    # Get markets
    exchange = ccxt.bittrex()
    markets = exchange.fetch_tickers()
    print('Number of markets={}'.format(len(markets)))
    # Altcoins
    altcoins = [dict(v, symbol=k.split('/')[0]) for k, v in markets.items() if '/BTC' in k]
    # Sort by baseVolume (Note: baseVolume might be None, so 'or 0')
    altcoins.sort(key=lambda x: float(x['quoteVolume'] or 0), reverse=True)
    print('Number of altcoins={}'.format(len(altcoins)))
    print([x['symbol'] for x in altcoins])

    # Get altcoin data from MongoDB
    collection = MongoClient().bittrex['tickers']
    chart_texts = []
    for i, symbol in enumerate([x['symbol'] for x in altcoins[:DISPLAY_NUMBER_OF_ALTCOINS]]):
        print('==========')
        print(symbol)
        tickers = list(collection.find(
            {'symbol': symbol, 'timestamp': {'$gte': now - timedelta(minutes=TARGET_MINUTES)}},
            {'_id': False},
        ).sort('timestamp', ASCENDING))
        # pprint(tickers)

        chart_dict = tickers_to_chart_dict(tickers)

        chart_text = textwrap.dedent(u"""
            {i}. {symbol}
            -----------------
            Latest price     : {latest_price:.8f} ({price_diff_rate:+.1%} from highest)
            Highest price    : {highest_price:.8f} ({highest_timestamp_diff} before)
            Price up-downs   : {price_up_downs}
            Price deviations : {price_diff_by_sigma} (σ)
            1 sigma price    : {sigma_percent:.1%}
        """).format(
            i=i + 1,
            symbol=symbol,
            latest_price=chart_dict['latest_price'],
            highest_price=chart_dict['highest_price'],
            highest_timestamp=chart_dict['highest_timestamp'].strftime('%m/%d %H:%M'),
            price_up_downs=', '.join(['{:+.1%}'.format(v) for v in chart_dict['price_up_downs']]),
            highest_timestamp_diff=chart_dict['highest_timestamp_diff'],
            price_diff_rate=(chart_dict['latest_price'] - chart_dict['highest_price']) / chart_dict['highest_price'],
            price_diff_by_sigma=', '.join(['{:.2f}'.format(v) for v in chart_dict['price_diff_by_sigma']]),
            sigma_percent=chart_dict['sigma_percent'],
        ).strip()
        print('----------')
        print(chart_text)
        chart_texts.append(chart_text)

    body = textwrap.dedent(u"""
    Date  : {date}
    Ticks : {minutes} mins x {ticks:,.0f} ({hours:,.0f} hours)

    {chart_texts}
    """).format(
        date=now.strftime('%Y/%m/%d %H:%M:%S'),
        minutes=MINUTES_PER_TICK,
        ticks=TARGET_MINUTES / MINUTES_PER_TICK,
        hours=TARGET_MINUTES / 60,
        chart_texts='\n\n'.join(chart_texts),
    ).strip()
    print('==========')
    print(body)

    email_client = EmailClient()
    # Send an email to myself
    email_client.send_test_email(u'[CC] Bittrex Tickers', body)


if __name__ == "__main__":
    main()
