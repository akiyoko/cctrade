# -*- coding: utf-8 -*-

from datetime import datetime
import os
import textwrap
from requests.packages.urllib3.exceptions import TimeoutError

from retry import retry
import tweepy

from email_client import EmailClient

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'env.py')
if os.path.exists(env_file):
    exec(open(env_file, 'rb').read())

FOLLOW_IDS = {
    '2312333412': '$ETH',  # @ethereumproject / Ethereum
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
            symbol = FOLLOW_IDS[str(status.user.id)]
            is_retweet = hasattr(status, 'retweeted_status')
            is_reply = (status.in_reply_to_user_id is not None)

            subject = u'CC Official Tweet Notification ({})'.format(symbol)
            body = textwrap.dedent(u"""
            Date     : {date}
            Name     : {name} (@{screen_name})
            Symbol   : {symbol}
            Followers count : {followers_count}
            Retweet? : {is_retweet}
            Reply?   : {is_reply}
            ==========
            {text}
            """).format(
                date=datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                name=status.user.name,
                screen_name=status.user.screen_name,
                symbol=symbol,
                followers_count='{:,}'.format(status.user.followers_count),
                is_retweet=is_retweet,
                is_reply=is_reply,
                text=status.text,
            ).strip()
            self.email_client.send_test_email(subject, body)

    def on_error(self, status_code):
        print('Got an error with status code: {}'.format(status_code))
        if status_code == 420:
            return False


@retry(TimeoutError, tries=3, delay=3)
def main():
    auth = tweepy.OAuthHandler(CONSUMER_KEY_2, CONSUMER_SECRET_2)
    auth.set_access_token(ACCESS_TOKEN_2, ACCESS_TOKEN_SECRET_2)

    listener = MyListener()
    stream = tweepy.Stream(auth=auth, listener=listener, retry_count=20)
    stream.filter(follow=FOLLOW_IDS.keys(), async=True)


if __name__ == "__main__":
    main()
