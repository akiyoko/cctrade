# -*- coding: utf-8 -*-

from utils import save_ticker_to_mongo


def main():
    save_ticker_to_mongo('binance', 'BTC/USDT')
    save_ticker_to_mongo('binance', 'ETH/USDT')


if __name__ == "__main__":
    main()
