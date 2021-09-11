# What this code does:
# Given a Twitter stream in JSON format, extract corresponding text stream, using only English tweets and a subset of the JSON object fields (e.g., date, id, hashtags, urls, text)
# Example run:
# python extract-json-to-text-stream.py test-syria-tweets.json json-to-text-stream-syria.json.txt

import codecs
from datetime import datetime
import json
#import requests
import os
import string
import sys
import time

file_timeordered_json_tweets = open(sys.argv[1], "r")
fout = open(sys.argv[2], "w")
users = ""
hashtags = ""
urls = ""
nfollowers = ""
nfriends = ""
#efficient line-by-line read of big files
for line in file_timeordered_json_tweets:
    tweet = json.loads(line)
    # print line
    tweet_gmttime = tweet['created_at']
    tweet_id = tweet['id']
    if 'retweeted_status' in tweet:
        text = tweet['retweeted_status']['text']
    else:
        text = tweet['text']
    # print tweet['hashtags']
    if 'hashtags' in tweet :
        hashtags = tweet['hashtags']
    # print hashtags
    if 'user_mentions' in tweet :
        users = [user_mention['screen_name'] for user_mention in tweet['user_mentions']]
    # print users
    if 'urls' in tweet :
        urls = tweet['urls']
    if 'followers_count' in tweet :
        nfollowers = tweet['user']['followers_count']
    if 'friends_count' in tweet :
        nfriends = tweet['user']['friends_count']
    try:
        c = time.strptime(tweet_gmttime.replace("+0000",''), '%a %b %d %H:%M:%S %Y')
    except:
        print "pb with tweet_gmttime", tweet_gmttime, line
        pass
    tweet_unixtime = int(time.mktime(c))
    # print [tweet_unixtime, tweet_gmttime, tweet_id, text, hashtags, users, urls, nfollowers, nfriends] , "\n"
    fout.write(str([tweet_unixtime, tweet_gmttime, tweet_id, text, hashtags, users, urls, nfollowers, nfriends]) + "\n")

fout.close()
file_timeordered_json_tweets.close()
