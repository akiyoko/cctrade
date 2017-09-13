# -*- coding: utf-8 -*-

import logging
import os
import textwrap
from datetime import datetime

import tweepy
from retrying import retry

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

FOLLOW_IDS = {
    '2312333412': 'ETH',  # @ethereumproject / Ethereum
    '385562752': 'LTC',  # @litecoin / Litecoin
    '1051053836': 'XRP',  # @Ripple / Ripple
    '2478439963': 'XMR',  # @monerocurrency / Monero
    '2592325530': 'NEO',  # @NEO_Blockchain / NEO
    '2338506822': 'DASH',  # @Dashpay / Dash
    '4736263474': 'LSK',  # @LiskHQ / Lisk
    '4633094778': 'ZEC',  # @zcashco / Zcash
    '4053977488': 'GNT',  # @golemproject / Golem
    '774689518767181828': 'SNT',  # @ethstatus / Status
    '2895317462': 'REP',  # @AugurProject / Augur
    '707515829798182912': 'WAVES',  # @wavesplatform / Waves
    '2804855658': 'FCT',  # @factom / Factom
    '2313671966': 'XEM',  # @nemofficial / NEM
    '734688391942524928': 'STRAT',  # @stratisplatform / Stratis
    '1322660676': 'MAID',  # @maidsafe / MaidSafeCoin
    '4020178512': 'PIVX',  # @_pivx / PIVX
    '2863324024': 'LBC',  # @LBRYio / LBRY Credits
    '2167563187': 'PPC',  # @PeercoinPPC / Peercoin
    '2460502890': 'XLM',  # @StellarOrg / Stellar Lumens
    '225710587': 'BCH',  # @BITCOINCASH (?) / Bitcoin Cash
    '2349043879': 'DCR',  # @decredproject / Decred
    '774791455680434176': 'ARK',  # @ArkEcosystem / Ark
    '4826209539': 'XVG',  # @vergecurrency / Verge
    '2510084300': 'BCN',  # @Bytecoin_BCN / Bytecoin
    '2266631022': 'DGB',  # @DigiByteCoin / Digibyte
    '816646997356777472': 'BNT',  # @BancorNetwork / Bancor Network Token
    '2243862290': 'NXT',  # @NxtCommunity / NXT
    '2275810436': 'VTC',  # @Vertcoin / Vertcoin
    '841424245938769920': 'BAT',  # @AttentionToken / Basic Attention Token
    '773009781644677120': 'QTUM',  # @QtumOfficial / Qtum
    '831847934534746114': 'OMG',  # @omise_go / OmiseGo
    '4585412124': 'PAY',  # @tenxwallet / TenX
    '3094365867': 'GAME',  # @gamecredits / GameCredits
    '773447880564731904': 'GBYTE',  # @ByteballOrg / Byteball
    '759252279862104064': 'ETC',  # @eth_classic (?) / Ethereum Classic
    '1729661822': 'OMNI',  # @Omni_Layer / Omni
    '864347902029709314': 'MCO',  # @monaco_card / Monaco
    '4131784210': 'PTOY',  # @patientory / Patientory
    '871853588540248064': 'FUN',  # @FunFairTech / FunFair
    '732169766450954240': 'WINGS',  # @wingsplatform / Wings
    '869908314292924416': 'ADX',  # @AdEx_Network / AdEx
    '2303710514': 'BTS',  # @_bitshares / BitShares
    '119060937': 'SYS',  # @syscoin / Syscoin
    '608922372': 'OK',  # @OKCashCrypto / OKCash
    '805450407078203392': 'EDG',  # @edgelessproject / Edgeless
    '769457743807844352': 'KMD',  # @KomodoPlatform / Komodo
    '4704538075': 'EGC',  # @EverGreenCoin_ / EverGreenCoin
    '3111739836': 'MTL',  # @metalpaysme / Metal
    '2575764354': 'NXS',  # @NxsEarth / Nexus
    '749620531062800384': '1ST',  # @firstbloodio / First Blood
    '4711101020': 'CVC',  # @civickey / Civic
    '723270672986845184': 'RISE',  # @RiseVisionTeam / Rise
    '812121371199164416': 'LUN',  # @LunyrInc / Lunyr
    '2532881881': 'NAV',  # @NAVCoin / NAV Coin
    '2366835468': 'EMC2',  # @einsteiniumcoin / Einsteinium
    '2436257148': 'VRC',  # @VeriCoin / VeriCoin
    '2917040642': 'UBQ',  # @ubiqsmart / Ubiq
    '2415756493': 'XMG',  # @Coin_Magi_XMG / Magi
    '2600194316': 'KORE',  # @NewKoreCoin / KoreCoin
    '345738416': 'SJCX',  # @storjproject / Storjcoin X
    '744075632997470208': 'ARDR',  # @ArdorPlatform / Ardor
    '711030662728437760': 'STEEM',  # @steemit / Steem
    '2591869950': 'MUE',  # @MonetaryUnit / MonetaryUnit
    '754632501667074049': 'TKN',  # @Monolith_web3 / TokenCard
    '826699259441328128': 'ZRX',  # @0xproject / 0x
    '901787503216050176': 'test',  # @yokoaki
    # '': '$',  # @ /
}


class MyListener(tweepy.StreamListener):
    def __init__(self):
        super(MyListener, self).__init__()
        self.email_client = EmailClient()

    def on_status(self, status):
        if str(status.user.id) in FOLLOW_IDS.keys():
            print('------------------------------')
            print('status={}'.format(status))
            logger.debug('CC official tweeted. user.id={}'.format(status.user.id))
            symbol = FOLLOW_IDS[str(status.user.id)]
            is_retweet = hasattr(status, 'retweeted_status')
            is_reply = (status.in_reply_to_user_id is not None)

            subject = u'[CC] Official Tweet Notification ({})'.format(symbol)
            body = textwrap.dedent(u"""
            Date     : {date}
            Name     : {name} (@{screen_name})
            Symbol   : {symbol}
            Followers count : {followers_count}
            Tweet count : {tweet_count}
            Retweet? : {is_retweet}
            Reply?   : {is_reply}
            ==========
            {text}
            ==========
            URL      : https://bittrex.com/Market/Index?MarketName=BTC-{symbol}
            """).format(
                date=datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                name=status.user.name,
                screen_name=status.user.screen_name,
                symbol=symbol,
                followers_count='{:,}'.format(status.user.followers_count),
                tweet_count='{:,}'.format(status.user.statuses_count),
                is_retweet=is_retweet,
                is_reply=is_reply,
                text=status.text,
            ).strip()
            self.email_client.send_test_email(subject, body)

    def on_error(self, status_code):
        print('Got an error with status code: {}'.format(status_code))
        logger.error('Got an error with status code: {}'.format(status_code))
        if status_code == 420:
            return False

    # See: https://stackoverflow.com/questions/14177327/tweepy-stops-after-a-few-hours
    def on_disconnect(self, notice):
        print('Got a disconnect signal with notice: {}'.format(notice))
        logger.error('Got a disconnect signal with notice: {}'.format(notice))
        return False


@retry(wait_random_min=3000, wait_random_max=5000)
def main():
    auth = tweepy.OAuthHandler(CONSUMER_KEY_2, CONSUMER_SECRET_2)
    auth.set_access_token(ACCESS_TOKEN_2, ACCESS_TOKEN_SECRET_2)

    listener = MyListener()
    stream = tweepy.Stream(auth=auth, listener=listener, retry_count=20)
    # Do not add 'async' option for retry
    stream.filter(follow=FOLLOW_IDS.keys())  # , async=True)


if __name__ == "__main__":
    main()
