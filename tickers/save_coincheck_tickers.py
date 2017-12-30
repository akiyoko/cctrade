# -*- coding: utf-8 -*-

from utils import save_ticker_to_mongo


def main():
    # Note: coincheck API returns not list but dict as follows.
    #       So, cannot use save_tickers_to_mongo_by_partial_currency_pair as it is.
    #       ```
    #       {'BTC/JPY': {'symbol': 'BTC/JPY', 'id': 'btc_jpy', 'limits': {}, 'precision': {}, 'base': 'BTC', 'quote': 'JPY'}}
    #       ```
    # save_tickers_to_mongo_by_partial_currency_pair('coincheck', '/JPY')
    save_ticker_to_mongo('coincheck', 'BTC/JPY')


if __name__ == "__main__":
    main()
