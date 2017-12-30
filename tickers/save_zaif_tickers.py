# -*- coding: utf-8 -*-

from utils import save_tickers_to_mongo_by_partial_currency_pair


def main():
    save_tickers_to_mongo_by_partial_currency_pair('zaif', '/JPY')


if __name__ == "__main__":
    main()
