# -*- coding: utf-8 -*-

import logging
import os
import textwrap
from datetime import datetime

import ccxt
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

# This is workaround.
# See https://github.com/ccxt-dev/ccxt/issues/227#issuecomment-331512509
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

BASE_CURRENCY = 'BTC'
DISPLAY_NUMBER_OF_ALTCOINS = 100  # TODO
MIN_VOLUME = 1  # TODO
EXCHANGES = [
    # # 1. Bitfinex (sometimes raises json.decoder.JSONDecodeError)
    # (ccxt.bitfinex({
    #     'apiKey': BITFINEX_KEY,
    #     'secret': BITFINEX_SECRET,
    # }), 'https://www.bitfinex.com/trading/{0}{1}'),
    # # 2. Bithumb
    # (ccxt.bithumb(), 'https://www.bithumb.com/trade/order/{0}'),
    # 3. Bittrex
    (ccxt.bittrex(), 'https://bittrex.com/Market/Index?MarketName={1}-{0}'),
    # 4. Poloniex
    (ccxt.poloniex(), 'https://poloniex.com/exchange#{1}_{0}'),
    # # 5. GDAX
    # (ccxt.gdax(), 'https://www.gdax.com/trade/{0}-{1}'),
    # # 7. Kraken
    # (ccxt.kraken(), 'https://www.kraken.com/charts'),
    # 8. HitBTC
    (ccxt.hitbtc2(), 'https://hitbtc.com/exchange/{0}-to-{1}'),
    # # 9. Bitstamp (sometimes raises HTTPError 404: NOT FOUND)
    # (ccxt.bitstamp(), 'https://www.bitstamp.net/'),
    # 10. bitFlyer (need apiKey and secret)
    # (ccxt.bitflyer(), 'https://lightning.bitflyer.jp/trade/{0}{1}'),
    # # 12. Gemini
    # (ccxt.gemini(), 'https://gemini.com/marketplace/'),
    # # 14. Binance
    # (ccxt.binance({
    #     'apiKey': BINANCE_KEY,
    #     'secret': BINANCE_SECRET,
    # }), 'https://www.binance.com/trade.html?symbol={0}_{1}'),
    # # 16. WEX
    # (ccxt.wex(), 'https://wex.nz/exchange/{0}_{1}'),
    # # 21. CEX.IO
    # (ccxt.cex(), 'https://cex.io/{0}-{1}'),
    # 22. YoBit
    (ccxt.yobit(), 'https://yobit.net/en/trade/{0}/{1}'),
    # # 24. Gatecoin
    # (ccxt.gatecoin(), 'https://gatecoin.com/marketData'),
    # 25. Liqui
    (ccxt.liqui(), 'https://liqui.io/#/exchange/{0}_{1}'),
    # # 26. OKEx
    # (ccxt.okex(), 'https://www.okex.com/'),
    # 43. Tidex
    (ccxt.tidex(), 'https://tidex.com/exchange/{0}/{1}'),
    # 52. Cryptopia
    (ccxt.cryptopia(), 'https://www.cryptopia.co.nz/Exchange/?market={0}_{1}'),
]


def main():
    now = datetime.now()

    # Get all markets
    res = requests.get('https://api.coinmarketcap.com/v1/ticker/')
    markets = res.json()
    print('Number of markets={}'.format(len(markets)))
    # Pop base currency and USDT (Tether)
    symbols = ['{}/{}'.format(x['symbol'], BASE_CURRENCY) for x in markets if x['symbol'] not in (BASE_CURRENCY, 'USDT')]
    print(symbols)
    # TODO: ZRX
    symbols.append('ZRX/{}'.format(BASE_CURRENCY))

    symbol_texts = []
    for symbol in symbols[:DISPLAY_NUMBER_OF_ALTCOINS]:
        ex_count = 0
        max_bid = 0
        max_bid_ex_name = ''
        max_bid_ex_url = ''
        max_bid_volume = 0
        min_ask = float('inf')
        min_ask_ex_name = ''
        min_ask_ex_url = ''
        min_ask_volume = 0
        for ex, ex_url in EXCHANGES:
            try:
                ex_ticker = ex.fetch_ticker(symbol)
            # TODO: Also catch urllib.error.HTTPError?
            except ccxt.errors.RequestTimeout:
                continue
            except TypeError:
                # Looks not to deal in this exchange
                continue
            except Exception as e:
                logger.warning(e)
                continue
            ex_count += 1
            ex_ask = ex_ticker.get('ask') or 0
            ex_bid = ex_ticker.get('bid') or 0
            ex_volume = ex_ticker.get('quoteVolume') or 0  # Volume
            # print('-' * 30)
            # print('{}'.format(ex.name))
            # print('Ask: {:.8f}'.format(ex_ask))
            # print('Bid: {:.8f}'.format(ex_bid))
            # print('Volume: {:.1f}'.format(ex_volume))
            if MIN_VOLUME < ex_volume:
                # Price to sell
                if max_bid < ex_bid:
                    max_bid = ex_bid
                    max_bid_ex_name = ex.name
                    max_bid_ex_url = ex_url
                    max_bid_volume = ex_volume
                # Price to buy
                if ex_ask < min_ask:
                    min_ask = ex_ask
                    min_ask_ex_name = ex.name
                    min_ask_ex_url = ex_url
                    min_ask_volume = ex_volume

        profit = max_bid - min_ask
        profit_rate = (profit / min_ask) if min_ask != 0 else 0  # TODO: else float('inf') ?
        if profit > 0:
            symbol_text = textwrap.dedent(u"""
            {symbol} ({ex_count})
            --------------------
            Sell at : {max_bid_ex_name:10} {max_bid_ex_url}
            Buy  at : {min_ask_ex_name:10} {min_ask_ex_url}
            Bid     : {max_bid:.8f} ({max_bid_volume:.1f} {base_currency}/day)
            Ask     : {min_ask:.8f} ({min_ask_volume:.1f} {base_currency}/day)
            Profit  : {profit:.8f} ({profit_rate:+.1%})
            """).format(
                symbol=symbol,
                base_currency=BASE_CURRENCY.lower(),
                ex_count=ex_count,
                max_bid_ex_name=max_bid_ex_name,
                max_bid_ex_url=max_bid_ex_url.format(*symbol.split('/')),
                max_bid=max_bid,
                max_bid_volume=max_bid_volume,
                min_ask_ex_name=min_ask_ex_name,
                min_ask_ex_url=min_ask_ex_url.format(*symbol.split('/')),
                min_ask=min_ask,
                min_ask_volume=min_ask_volume,
                profit=profit,
                profit_rate=profit_rate,
            ).strip()
            # print('=' * 40)
            # print(symbol_text)
            symbol_texts.append((symbol_text, profit_rate))

    # Sort by profit rate
    symbol_texts = [x[0] for x in sorted(symbol_texts, key=lambda x: x[1], reverse=True)]

    body = textwrap.dedent(u"""
    Date  : {date}
    Top {number_of_altcoins} Currencies from {number_of_exchanges} Exchanges
    Volume Threshold : {min_volume} {base_currency}/day

    {symbol_text}
    """).format(
        date=now.strftime('%Y/%m/%d %H:%M:%S'),
        number_of_altcoins=DISPLAY_NUMBER_OF_ALTCOINS,
        number_of_exchanges=len(EXCHANGES),
        min_volume=MIN_VOLUME,
        base_currency=BASE_CURRENCY.lower(),
        symbol_text='\n\n'.join(symbol_texts),
    ).strip()
    print(body)

    email_client = EmailClient()
    # Send an email to myself
    email_client.send_test_email(u'[CC] Check Price Difference (by {})'.format(BASE_CURRENCY), body)


if __name__ == "__main__":
    main()
