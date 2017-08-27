# -*- coding: utf-8 -*-

import textwrap
from datetime import datetime, timedelta

from pymongo import MongoClient, DESCENDING

from email_client import EmailClient

INTERVAL_MINUTES = 30
SYMBOL_DISPLAY_SIZE = 50
HASHTAG_DISPLAY_SIZE = 50

if __name__ == "__main__":
    now = datetime.now()

    # Symbols
    db_symbols = MongoClient().cctweet['symbols']
    symbols = list(db_symbols.find({'time': {'$exists': False}}, {'_id': False}, sort=[('count', DESCENDING)]))
    for symbol in symbols:
        # TODO: Need fix? INTERVAL_MINUTES * 1.5
        prev = db_symbols.find_one(
            {'key': symbol['key'], 'time': {'$gte': now - timedelta(minutes=INTERVAL_MINUTES * 1.5)}},
            sort=[('time', DESCENDING)])
        if prev is not None:
            symbol.update({'diff': float(symbol['count'] - prev['count']) / float(prev['count'])})
        else:
            symbol.update({'diff': float('inf')})
    # Hashtags
    db_hashtags = MongoClient().cctweet['hashtags']
    hashtags = list(db_hashtags.find({'time': {'$exists': False}}, {'_id': False}, sort=[('count', DESCENDING)]))
    for hashtag in hashtags:
        # TODO: Need fix? INTERVAL_MINUTES * 1.5
        prev = db_hashtags.find_one(
            {'key': hashtag['key'], 'time': {'$gte': now - timedelta(minutes=INTERVAL_MINUTES * 1.5)}},
            sort=[('time', DESCENDING)])
        if prev is not None:
            hashtag.update({'diff': float(hashtag['count'] - prev['count']) / float(prev['count'])})
        else:
            hashtag.update({'diff': float('inf')})

    # Update time
    db_symbols.update({'time': {'$exists': False}}, {'$set': {'time': now}}, multi=True)
    db_hashtags.update({'time': {'$exists': False}}, {'$set': {'time': now}}, multi=True)

    # Cleanup
    db_symbols.remove({'time': {'$lt': now - timedelta(hours=24)}})
    db_hashtags.remove({'time': {'$lt': now - timedelta(hours=24)}})

    body = textwrap.dedent(u"""
    Date     : {date}

    $ Top Symbols
    =============
    {top_symbols}

    # Top Hashtags
    ==============
    {top_hashtags}
    """).format(
        date=now.strftime('%Y/%m/%d %H:%M'),
        top_symbols='\n'.join([u'{}: {} ({})'.format(d['key'], d['count'], '{:+.0%}'.format(d['diff'])) for d in symbols[0:SYMBOL_DISPLAY_SIZE]]),
        top_hashtags='\n'.join([u'{}: {} ({})'.format(d['key'], d['count'], '{:+.0%}'.format(d['diff'])) for d in hashtags[0:HASHTAG_DISPLAY_SIZE]]),
    ).strip()

    email_client = EmailClient()
    email_client.send_test_email(u'CC Tweet Summary', body)
