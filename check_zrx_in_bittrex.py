# -*- coding: utf-8 -*-

import ccxt

from email_client import EmailClient


def main():
    # Get markets
    exchange = ccxt.bittrex()
    markets = exchange.fetch_tickers()

    if 'ZRX/BTC' in markets.keys():
        email_client = EmailClient()
        email_client.send_test_email(u'[ZRX] Alert!!', u'This is an notification that ZRX has been on live in bittrex!')


if __name__ == "__main__":
    main()
