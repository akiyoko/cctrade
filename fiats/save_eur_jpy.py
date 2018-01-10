# -*- coding: utf-8 -*-

from utils import save_fiat_rate_to_mongo


def main():
    save_fiat_rate_to_mongo('EUR/JPY')


if __name__ == "__main__":
    main()
