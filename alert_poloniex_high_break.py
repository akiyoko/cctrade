# -*- coding: utf-8 -*-

from datetime import datetime
import textwrap
import time

import pandas as pd
import poloniex

from email_client import EmailClient

DISPLAY_NUMS = 50  # TODO
MINUTES_PER_TICK = 15
TARGET_HOURS = 24 * 7 * 4
TICKS = int(TARGET_HOURS * 60 / MINUTES_PER_TICK)


def get_chart_data(currency_pair, minutes=5, ticks=12*24):
    polo = poloniex.Poloniex(timeout=10, coach=True)
    now = time.time()
    # print("now={}".format(now))
    # current_datetime = datetime.fromtimestamp(now)
    # print("datetime={}".format(datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')))
    candlestick_period = polo.MINUTE * minutes
    c = polo.returnChartData(currency_pair, period=candlestick_period, start=now - candlestick_period * ticks)

    # print('c={}'.format(c))
    df = pd.DataFrame(c)
    df['date'] = df['date'].apply(lambda x: datetime.fromtimestamp(x))
    df = df.set_index('date')
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['quoteVolume'] = df['quoteVolume'].astype(float)
    df['price_diff'] = df['close'] - df['close'].shift(1)
    df['price_diff_rate'] = df['price_diff'] / df['close'].shift(1)
    df['volume_diff'] = df['volume'] - df['volume'].shift(1)
    df['volume_diff_rate'] = df['volume_diff'] / df['volume'].shift(1)

    print("size of df={}".format(len(df)))
    print(df)
    highest_timestamp = df['high'].idxmax()
    print("highest_date={}".format(highest_timestamp))
    print("highest_date.__class__={}".format(highest_timestamp.__class__))
    sr_highest = df.loc[highest_timestamp]
    highest_price = sr_highest['high']
    print('sr_highest={}'.format(sr_highest))
    print("highest_price={}".format(highest_price))
    print("highest_price.__class__={}".format(highest_price.__class__))
    print('df["high"].max()={}'.format(df['high'].max()))
    df_sliced = df[(datetime.fromtimestamp(now - candlestick_period * 5) <= df.index)]
    print('df_sliced={}'.format(df_sliced))
    print('size of df_sliced={}'.format(len(df_sliced)))
    df_latest = df.tail(1)
    latest_price = df_latest['close'].values[0]
    latest_timestamp = df_latest.index[0]
    print('highest_timestamp={}'.format(highest_timestamp))
    print('latest_timestamp={}'.format(latest_timestamp))
    timestamp_diff = (latest_timestamp - highest_timestamp)
    print('timestamp_diff={}'.format(timestamp_diff))
    latest_volume = df_latest['volume'].values[0]
    total_volume = df['volume'].sum()
    # price_diff = df_latest['price_diff'].values[0]
    price_up_downs = df.tail(3)['price_diff_rate'].values
    volume_up_downs = df.tail(3)['volume_diff_rate'].values
    latest_volumes = df.tail(3)['volume'].values
    print('price_up_downs={}'.format(price_up_downs))
    # volume_diff = df_latest['volume_diff'].values[0]
    print('latest_volume={}'.format(latest_volume))
    print('total_volume={}'.format(total_volume))

    data = dict(
        currency_pair='{1}/{0}'.format(*(currency_pair.split('_'))),
        latest_price='{:.8f}'.format(latest_price),
        latest_timestamp=latest_timestamp.strftime('%m/%d %H:%M'),
        latest_volume='{:.1f}'.format(latest_volume),
        highest_price='{:.8f}'.format(highest_price),
        highest_timestamp=highest_timestamp.strftime('%m/%d %H:%M'),
        # price_diff='{:+.1%}'.format(price_diff / (latest_price - price_diff)),
        price_up_downs=', '.join(['{:+.1%}'.format(v) for v in price_up_downs]),
        # volume_diff='{:+.1%}'.format(volume_diff / (latest_volume - volume_diff)),
        volume_up_downs=', '.join(['{:+.1%}'.format(v) for v in volume_up_downs]),
        latest_volumes=', '.join(['{:.1f}'.format(v) for v in latest_volumes]),
        timestamp_diff=timestamp_diff,
        price_rate='{:+.1%}'.format((latest_price - highest_price) / highest_price),
        latest_volumes_rate='{:.1%}'.format(latest_volumes.sum() / total_volume),
    )
    print("data={}".format(data))
    return data


def main():
    # Get currency pairs sorted by 24-hour volume
    polo = poloniex.Poloniex(timeout=10, coach=True)
    sorted_tickers = sorted(polo.returnTicker().items(), key=lambda x: float(x[1]['baseVolume']), reverse=True)
    currency_pairs = [k for k, v in sorted_tickers if 'BTC_' in k]

    chart_texts = []
    for currency_pair in currency_pairs[0:DISPLAY_NUMS]:
        print("currency_pair={}".format(currency_pair))
        data = get_chart_data(currency_pair, MINUTES_PER_TICK, TICKS)
        chart_texts.append(textwrap.dedent(u"""
        {currency_pair}
        Latest price      : {latest_price} ({price_rate} from highest)
        Latest timestamp  : {latest_timestamp}
        Highest price     : {highest_price}
        Highest timestamp : {highest_timestamp} ({timestamp_diff} before)
        Price up-downs    : {price_up_downs} (past 3 ticks)
        Latest volumes    : {latest_volumes} (past 3 ticks, {latest_volumes_rate} of total)
        Volume up-downs   : {volume_up_downs} (past 3 ticks)
        """).strip().format(**data))

    body = textwrap.dedent(u"""
    Date  : {date}
    Ticks : {minutes} mins x {ticks} ({hours} hours)

    {chart_texts}
    """).format(
        date=datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        minutes=MINUTES_PER_TICK,
        ticks=TICKS,
        hours=TARGET_HOURS,
        chart_texts='\n\n'.join(chart_texts),
    ).strip()

    print('----------')
    print(body)
    print('----------')

    email_client = EmailClient()
    # Send an email to myself
    email_client.send_test_email(u"Poloniex high break", body)


if __name__ == "__main__":
    main()
