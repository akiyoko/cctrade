# -*- coding: utf-8 -*-

import logging
import os
import textwrap
from datetime import datetime

import pandas as pd
from pprint import pprint
import requests

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


def main():
    # Get all markets
    res = requests.get('https://api.coinmarketcap.com/v1/ticker/')
    markets = res.json()
    print('Number of markets={}'.format(len(markets)))

    # Sort by 24h_volume_usd (Note: some 24h_volume_usd are None, so 'or 0')
    markets.sort(key=lambda x: float(x['24h_volume_usd'] or 0), reverse=True)
    # Pop BTC and USDT (Tether)
    markets = [x for x in markets if x['symbol'] not in ('BTC', 'USDT')]
    # pprint(markets)

    # Get Bitcoin market
    res = requests.get('https://api.coinmarketcap.com/v1/ticker/{}/'.format('bitcoin'))
    bitcoin = res.json()[0]

    df = pd.DataFrame(markets)
    df['price_usd'] = df['price_usd'].astype(float)
    df['price_btc'] = df['price_btc'].astype(float)
    df['24h_volume_usd'] = df['24h_volume_usd'].astype(float)
    df['market_cap_usd'] = df['market_cap_usd'].astype(float)
    df['available_supply'] = df['available_supply'].astype(float)
    df['total_supply'] = df['total_supply'].astype(float)
    df['percent_change_1h'] = df['percent_change_1h'].astype(float)
    df['percent_change_24h'] = df['percent_change_24h'].astype(float)
    df['percent_change_7d'] = df['percent_change_7d'].astype(float)
    df['last_updated'] = df['last_updated'].apply(lambda x: datetime.fromtimestamp(float(x)))
    print(df[0:10])

    df_top10 = df[0:10]
    df_top20 = df[0:20]
    df_top30 = df[0:30]
    df_top50 = df[0:50]
    df_top51_100 = df[50:100]
    df_top100 = df[0:100]
    body = textwrap.dedent(u"""
    Bitcoin
    =======
    (1h)  price change : {bitcoin_1h_change:+.1f}%
    (24h) price change : {bitcoin_24h_change:+.1f}%
    (7d)  price change : {bitcoin_7d_change:+.1f}%
    
    Top 10 markets
    ==============
    (1h)  price up/down : {top10_1h_up} / {top10_1h_down}
    (1h)  price mean    : {top10_1h_mean:+.1f}%
    (24h) price up/down : {top10_24h_up} / {top10_24h_down}
    (24h) price mean    : {top10_24h_mean:+.1f}%
    (7d)  price up/down : {top10_7d_up} / {top10_7d_down}
    (7d)  price mean    : {top10_7d_mean:+.1f}%

    Top 20 markets
    ==============
    (1h)  price up/down : {top20_1h_up} / {top20_1h_down}
    (1h)  price mean    : {top20_1h_mean:+.1f}%
    (24h) price up/down : {top20_24h_up} / {top20_24h_down}
    (24h) price mean    : {top20_24h_mean:+.1f}%
    (7d)  price up/down : {top20_7d_up} / {top20_7d_down}
    (7d)  price mean    : {top20_7d_mean:+.1f}%

    Top 30 markets
    ==============
    (1h)  price up/down : {top30_1h_up} / {top30_1h_down}
    (1h)  price mean    : {top30_1h_mean:+.1f}%
    (24h) price up/down : {top30_24h_up} / {top30_24h_down}
    (24h) price mean    : {top30_24h_mean:+.1f}%
    (7d)  price up/down : {top30_7d_up} / {top30_7d_down}
    (7d)  price mean    : {top30_7d_mean:+.1f}%

    Top 50 markets
    ==============
    (1h)  price up/down : {top50_1h_up} / {top50_1h_down}
    (1h)  price mean    : {top50_1h_mean:+.1f}%
    (24h) price up/down : {top50_24h_up} / {top50_24h_down}
    (24h) price mean    : {top50_24h_mean:+.1f}%
    (7d)  price up/down : {top50_7d_up} / {top50_7d_down}
    (7d)  price mean    : {top50_7d_mean:+.1f}%

    Top 51-100 markets
    ==============
    (1h)  price up/down : {top51_100_1h_up} / {top51_100_1h_down}
    (1h)  price mean    : {top51_100_1h_mean:+.1f}%
    (24h) price up/down : {top51_100_24h_up} / {top51_100_24h_down}
    (24h) price mean    : {top51_100_24h_mean:+.1f}%
    (7d)  price up/down : {top51_100_7d_up} / {top51_100_7d_down}
    (7d)  price mean    : {top51_100_7d_mean:+.1f}%

    Top 100 markets
    ===============
    (1h)  price up/down : {top100_1h_up} / {top100_1h_down}
    (1h)  price mean    : {top100_1h_mean:+.1f}%
    (24h) price up/down : {top100_24h_up} / {top100_24h_down}
    (24h) price mean    : {top100_24h_mean:+.1f}%
    (7d)  price up/down : {top100_7d_up} / {top100_7d_down}
    (7d)  price mean    : {top100_7d_mean:+.1f}%
    """).format(
        bitcoin_1h_change=float(bitcoin['percent_change_1h']),
        bitcoin_24h_change=float(bitcoin['percent_change_24h']),
        bitcoin_7d_change=float(bitcoin['percent_change_7d']),

        top10_1h_up=len(df_top10[df_top10['percent_change_1h'] > 0]),
        top10_1h_down=len(df_top10[df_top10['percent_change_1h'] <= 0]),
        top10_1h_mean=df_top10.mean()['percent_change_1h'],
        top10_24h_up=len(df_top10[df_top10['percent_change_24h'] > 0]),
        top10_24h_down=len(df_top10[df_top10['percent_change_24h'] <= 0]),
        top10_24h_mean=df_top10.mean()['percent_change_24h'],
        top10_7d_up=len(df_top10[df_top10['percent_change_7d'] > 0]),
        top10_7d_down=len(df_top10[df_top10['percent_change_7d'] <= 0]),
        top10_7d_mean=df_top10.mean()['percent_change_7d'],

        top20_1h_up=len(df_top20[df_top20['percent_change_1h'] > 0]),
        top20_1h_down=len(df_top20[df_top20['percent_change_1h'] <= 0]),
        top20_1h_mean=df_top20.mean()['percent_change_1h'],
        top20_24h_up=len(df_top20[df_top20['percent_change_24h'] > 0]),
        top20_24h_down=len(df_top20[df_top20['percent_change_24h'] <= 0]),
        top20_24h_mean=df_top20.mean()['percent_change_24h'],
        top20_7d_up=len(df_top20[df_top20['percent_change_7d'] > 0]),
        top20_7d_down=len(df_top20[df_top20['percent_change_7d'] <= 0]),
        top20_7d_mean=df_top20.mean()['percent_change_7d'],

        top30_1h_up=len(df_top30[df_top30['percent_change_1h'] > 0]),
        top30_1h_down=len(df_top30[df_top30['percent_change_1h'] <= 0]),
        top30_1h_mean=df_top30.mean()['percent_change_1h'],
        top30_24h_up=len(df_top30[df_top30['percent_change_24h'] > 0]),
        top30_24h_down=len(df_top30[df_top30['percent_change_24h'] <= 0]),
        top30_24h_mean=df_top30.mean()['percent_change_24h'],
        top30_7d_up=len(df_top30[df_top30['percent_change_7d'] > 0]),
        top30_7d_down=len(df_top30[df_top30['percent_change_7d'] <= 0]),
        top30_7d_mean=df_top30.mean()['percent_change_7d'],

        top50_1h_up=len(df_top50[df_top50['percent_change_1h'] > 0]),
        top50_1h_down=len(df_top50[df_top50['percent_change_1h'] <= 0]),
        top50_1h_mean=df_top50.mean()['percent_change_1h'],
        top50_24h_up=len(df_top50[df_top50['percent_change_24h'] > 0]),
        top50_24h_down=len(df_top50[df_top50['percent_change_24h'] <= 0]),
        top50_24h_mean=df_top50.mean()['percent_change_24h'],
        top50_7d_up=len(df_top50[df_top50['percent_change_7d'] > 0]),
        top50_7d_down=len(df_top50[df_top50['percent_change_7d'] <= 0]),
        top50_7d_mean=df_top50.mean()['percent_change_7d'],

        top51_100_1h_up=len(df_top51_100[df_top51_100['percent_change_1h'] > 0]),
        top51_100_1h_down=len(df_top51_100[df_top51_100['percent_change_1h'] <= 0]),
        top51_100_1h_mean=df_top51_100.mean()['percent_change_1h'],
        top51_100_24h_up=len(df_top51_100[df_top51_100['percent_change_24h'] > 0]),
        top51_100_24h_down=len(df_top51_100[df_top51_100['percent_change_24h'] <= 0]),
        top51_100_24h_mean=df_top51_100.mean()['percent_change_24h'],
        top51_100_7d_up=len(df_top51_100[df_top51_100['percent_change_7d'] > 0]),
        top51_100_7d_down=len(df_top51_100[df_top51_100['percent_change_7d'] <= 0]),
        top51_100_7d_mean=df_top51_100.mean()['percent_change_7d'],

        top100_1h_up=len(df_top100[df_top100['percent_change_1h'] > 0]),
        top100_1h_down=len(df_top100[df_top100['percent_change_1h'] <= 0]),
        top100_1h_mean=df_top100.mean()['percent_change_1h'],
        top100_24h_up=len(df_top100[df_top100['percent_change_24h'] > 0]),
        top100_24h_down=len(df_top100[df_top100['percent_change_24h'] <= 0]),
        top100_24h_mean=df_top100.mean()['percent_change_24h'],
        top100_7d_up=len(df_top100[df_top100['percent_change_7d'] > 0]),
        top100_7d_down=len(df_top100[df_top100['percent_change_7d'] <= 0]),
        top100_7d_mean=df_top100.mean()['percent_change_7d'],
    ).strip()

    email_client = EmailClient()
    # Send an email to myself
    email_client.send_test_email(u'[CC] Entire Market Mood', body)


if __name__ == "__main__":
    main()
