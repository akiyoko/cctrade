# -*- coding: utf-8 -*-

from utils import save_ticker_to_mongo


def main():
    save_ticker_to_mongo('bitfinex', 'BTC/USD')
    save_ticker_to_mongo('bitfinex', 'ETH/USD')


if __name__ == "__main__":
    main()
