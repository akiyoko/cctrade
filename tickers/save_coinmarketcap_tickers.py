# -*- coding: utf-8 -*-

from utils import save_ticker_to_mongo


def main():
    save_ticker_to_mongo('coinmarketcap', 'BTC/USD')
    save_ticker_to_mongo('coinmarketcap', 'ETH/USD')


if __name__ == "__main__":
    main()
