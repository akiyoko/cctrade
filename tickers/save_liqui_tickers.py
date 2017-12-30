# -*- coding: utf-8 -*-

from utils import save_ticker_to_mongo


def main():
    save_ticker_to_mongo('liqui', 'BTC/USDT')
    save_ticker_to_mongo('liqui', 'ETH/USDT')


if __name__ == "__main__":
    main()
