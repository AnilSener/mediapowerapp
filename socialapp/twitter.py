__author__ = 'root'
from twython import TwythonStreamer
from socialapp.models import Tweet,TwitterUser,BoundingBox,TweetNode,HashTag
import configparser
config = configparser.ConfigParser()
config.read('../app.conf')
from django.contrib.auth import authenticate
import datetime
#from background_task import background
####################################################################
consumer_key="Vs7V2k4vPWMMyTFqLzqPkM6wE"
consumer_secret="aWNRzh74LUT1fuW35y6VzRDtvuimQ4LjFGMnMMkEXI0Y9LSpkf"

access_token="258113369-63Y2Cqr9q0Bo02WU4AS8Bjiv3JnHP2Us7HimK26G"
access_token_secret="Z4Sf9EyLbOJ4jPI5WlZPZUyv3OwluuZXiKXn0pamk8Dly"
###################################################################
#@background(schedule=datetime.datetime.now())
from mediapowerapp import celery_app
from time import sleep
@celery_app.task()
def exec_Twitter_Streamer():
    class MyStreamer(TwythonStreamer):
        def on_success(self, data):
            if 'text' in data:
                print(data)
                print(data['text'].encode('utf-8'))
            #try:
                authenticate(username='default', password='defaultpassword')
                qs=TwitterUser.objects.filter(userID=data["user"]["id_str"])
                u = TwitterUser()
                if len(qs[:])>0:
                    u=qs[:1].get()
                u.userID = data["user"]['id_str']#Should be uniqueId!!! Set as a qunique index
                u.userName = data["user"]["name"]
                u.followersCount = data["user"]["followers_count"]
                u.friendsCount = data["user"]["friends_count"]
                u.retweetCount = data["retweet_count"]
                u.isGeoEnabled = data["user"]['geo_enabled']
                u.language = data["user"]['lang']

                t=Tweet()
                coord=data["place"]["bounding_box"]['coordinates'][0]
                if coord[0][0]==coord[1][0] and coord[0][1]==coord[1][1]:
                    t.geopoint = coord[0];print "geom trick"
                else:
                    t.geometry=[[coord[0],coord[1],coord[2],coord[3],coord[0]]]
                if data["geo"]!=None:
                    t.geopoint = data["geo"]["coordinates"]
                t.placeId = data["place"]["id"]
                t.placeFullName = data["place"]["full_name"]
                t.placeName = data["place"]["name"]
                t.countryCode = data["place"]["country_code"]
                t.placeType = data["place"]["place_type"]
                t.language = data["lang"]
                t.text = data['text']
                t.createdAt = data["created_at"]
                #print data["entities"]["hashtags"]
                t.timestamp = datetime.datetime.fromtimestamp(long(data["timestamp_ms"])/1e3)
                t.isRetweeted = data["retweeted"]
                t.isFavorited= data["favorited"]
                t.favoriteCount = data["favorite_count"]
                t.retweetCount = data["retweet_count"]
                t.trends = data["entities"]["trends"]
                #t.hashtags = data["entities"]["hashtags"]
                t.symbols = data["entities"]["symbols"]
                t.urls = data["entities"]["urls"]
                t.save()

                tn=TweetNode.objects.create(objectID=str(t._object_key),tweetID=data["id"],in_reply_to_status_id=data["in_reply_to_status_id"])
                t.cleaned_text = cleanTweet(t,tn,u)
                if data["in_reply_to_status_id"]!=None:
                    t.calculate_Sentiment_Scores()
                    print t.pos_Score
                    print t.obj_Score
                    print t.neg_Score
                if tn.in_reply_to_status_id!=None:
                    qs=TweetNode.objects.filter(tweetID=tn.in_reply_to_status_id)
                    if len(qs[:])>0:
                        parent_tn=qs[:1].get()
                        parent_tn.replies.add(tn)
                        parent_tn.save()

    stream = MyStreamer(consumer_key, consumer_secret,access_token,access_token_secret)

    #stream.statuses.filter(follow=["Ford","Forduk","FordAutoShows","FordEu"])
    stream.statuses.filter(locations=[-74.2591,40.4774,-73.7002,40.9176],replies=all,language="en")
    #stream.statuses.filter(locations=[-74.2591,40.4774,-73.7002,40.9176])
    #stream.statuses.filter(follow=["Ford","Forduk","FordAutoShows","FordEu"],replies=all,language="en")
    #stream.statuses.filter(follow=["Ford","VW","Volkswagen","Forduk","FordAutoShows","FordEu","Toyota"])
    #Enable Count in IBM server
    #stream.statuses.filter(count=50000)
import HTMLParser
html_parser=HTMLParser.HTMLParser()
import re
def cleanTweet(t,tn,u):
    text=html_parser.unescape(t.text)
    text=re.sub(r"http\S+", "", text)
    text=re.sub(r"ftp\S+", "", text)
    urls=[str(ur['url']) for ur in t.urls]
    text=text.encode('ascii','ignore')
    for word in text.split():
        if word.startswith("@") or word in urls:
            text=text.replace(word,"")
        elif word.startswith("#"):
            qs=HashTag.objects.filter(tag=word)
            hash_tag=None
            if len(qs[:])>0:
                hash_tag=qs[:1].get()
            else:
                hash_tag=HashTag.objects.create(tag=word)
            tn.hashtags.add(hash_tag)
            tn.save()
            previous_user_tags=[obj.tag for obj in list(u.hashtags.all())]
            print "previous hashtags",previous_user_tags
            if not word in previous_user_tags:
                u.tweets.add(tn)
                u.hashtags.add(hash_tag)
                u.save()
            text=text.replace(word,"")
    print text
    #text=text.lower()
    return text
"""
Rest API
from twython import Twython
twitter = Twython()

api_url = 'https://api.twitter.com/1.1/search/tweets.json'
constructed_url = twitter.construct_api_url(api_url, q='python',
result_type='popular')
print constructed_url
https://api.twitter.com/1.1/search/tweets.json?q=python&result_type=popular
"""


#twitter = Twython(consumer_key, consumer_secret,access_token,access_token_secret, oauth_version=2)
#print(twitter.get_home_timeline())

