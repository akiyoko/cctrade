# -*- coding: utf-8 -*-

from datetime import datetime
import textwrap
import time

import pandas as pd
import poloniex

from email_client import EmailClient

DISPLAY_NUMS = 30
MINUTES = 3
TICKS = 10


def get_volumes(currency_pair, volume_24h, minutes=1, ticks=10):
    polo = poloniex.Poloniex(timeout=10, coach=True)
    now = time.time()
    period = polo.MINUTE * minutes
    hists = polo.marketTradeHist(currency_pair, start=now - period * ticks)

    df = pd.DataFrame(hists)
    df = df.set_index('date')
    df['amount'] = df['amount'].astype(float)
    df['rate'] = df['rate'].astype(float)
    df['total'] = df['total'].astype(float)
    # Set timezone
    df.index = pd.to_datetime(df.index, utc=True).tz_convert('Asia/Tokyo')

    last_prices = []
    up_downs = []
    buy_volumes = []
    sell_volumes = []
    volume_diffs = []
    print("len(df)={}".format(len(df)))
    for start in range(-ticks, 0):
        end = start + 1
        print("start={}, end={}".format(start, end))
        df_sliced = df[(datetime.fromtimestamp(now + period * start) <= df.index) & (df.index < datetime.fromtimestamp(now + period * end))]
        if not df_sliced.empty:
            print("df_sliced={}".format(df_sliced))
            print("df_sliced.head(1)={}".format(df_sliced.head(1)))
            print("df_sliced.tail(1)={}".format(df_sliced.tail(1)))
            first_price = df_sliced.head(1)['rate'].values[0] if not last_prices else last_prices[-1]
            last_price = df_sliced.tail(1)['rate'].values[0]
            last_prices.append(last_price)
            up_downs.append('{:.2%}'.format((last_price - first_price) / first_price))
            buy_volume = df_sliced[df_sliced['type'] == 'buy']['total'].sum()
            buy_volumes.append(buy_volume)
            sell_volume = df_sliced[df_sliced['type'] == 'sell']['total'].sum()
            sell_volumes.append(sell_volume)
            volume_diffs.append(buy_volume - sell_volume)
        else:
            print("Dataframe is empty!!!!")
            # last_prices.append(last_price)
            up_downs.append('-')
            buy_volumes.append(0)
            sell_volumes.append(0)
            volume_diffs.append(0)
    print("total={}".format(df['total'].sum()))

    return textwrap.dedent(u"""
        {currency_pair}
        First/Last price : {first_price} / {last_price} ({price_diff})
        Up-downs         : {up_downs}
        Buy volumes      : {buy_volumes} ({buy_volumes_sum})
        Sell volumes     : {sell_volumes} ({sell_volumes_sum})
        Buy-Sell volumes : {volume_diffs} ({volume_diffs_sum})
        24-hour volume   : {volume_24h} ({priod_ticks}-mins buy: {buy_volumes_rate}, sell: {sell_volumes_rate})
    """).format(
        currency_pair='{1}/{0}'.format(*(currency_pair.split('_'))),
        first_price='{:.8f}'.format(first_price),
        last_price='{:.8f}'.format(last_price),
        price_diff='{:.2%}'.format((last_price - first_price) / first_price),
        up_downs=', '.join(up_downs),
        buy_volumes=', '.join(['{:.0f}'.format(v) for v in buy_volumes]),
        buy_volumes_sum='{:.0f}'.format(sum(buy_volumes)),
        buy_volumes_rate='{:.2%}'.format(sum(buy_volumes) / volume_24h),
        sell_volumes=', '.join(['{:.0f}'.format(v) for v in sell_volumes]),
        sell_volumes_sum='{:.0f}'.format(sum(sell_volumes)),
        sell_volumes_rate='{:.2%}'.format(sum(sell_volumes) / volume_24h),
        volume_diffs=', '.join(['{:.0f}'.format(v) for v in volume_diffs]),
        volume_diffs_sum='{:.0f}'.format(sum(volume_diffs)),
        volume_24h='{:.0f}'.format(volume_24h),
        priod_ticks=minutes * ticks,
    ).strip()


def main():
    # Get currency pairs sorted by 24-hour volume
    polo = poloniex.Poloniex(timeout=10, coach=True)
    sorted_tickers = sorted(polo.returnTicker().items(), key=lambda x: float(x[1]['baseVolume']), reverse=True)
    currency_pairs = [(k, float(v['baseVolume'])) for k, v in sorted_tickers if 'BTC_' in k or k == 'USDT_BTC']

    volume_texts = []
    for currency_pair, volume_24h in currency_pairs[0:DISPLAY_NUMS]:
        print("currency_pair={}".format(currency_pair))
        volume_texts.append(get_volumes(currency_pair, volume_24h, MINUTES, TICKS))

    body = textwrap.dedent(u"""
    Date  : {date}
    Ticks : {minutes} mins x {ticks}

    {volume_texts}
    """).format(
        date=datetime.now().strftime('%Y/%m/%d %H:%M'),
        minutes=MINUTES,
        ticks=TICKS,
        volume_texts='\n\n'.join(volume_texts),
    ).strip()

    print('----------')
    print(body)
    print('----------')

    email_client = EmailClient()
    # Send an email to myself
    email_client.send_test_email(u"Poloniex trade volumes", body)


if __name__ == "__main__":
    main()
