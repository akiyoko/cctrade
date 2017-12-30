# -*- coding: utf-8 -*-

from utils import save_ticker_to_mongo


def main():
    save_ticker_to_mongo('yobit', 'BTC/USD')
    save_ticker_to_mongo('yobit', 'ETH/USD')


if __name__ == "__main__":
    main()
