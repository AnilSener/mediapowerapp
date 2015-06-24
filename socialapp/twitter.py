__author__ = 'root'
from twython import TwythonStreamer,Twython,TwythonError
from socialapp.models import Tweet,TwitterUser,BoundingBox,TweetNode,HashTag,TwitterRegistry,Subscriber
import configparser
config = configparser.ConfigParser()
config.read('../app.conf')
from django.contrib.auth import authenticate
import datetime
from pytz import timezone
from time import sleep
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
    class SubscriberUserStreamer(TwythonStreamer):
        def on_success(self, data):
            if 'text' in data:
                print(data)
                print(data['text'].encode('utf-8'))
                try:
                    authenticate(username='default', password='defaultpassword')
                    t_qs=Tweet.objects.filter(tweetID=data["id"])
                    if len(t_qs[:])==0:
                        qs=TwitterUser.objects.filter(userID=data["user"]["id_str"])
                        u = TwitterUser()
                        if len(qs[:])>0:
                            u=qs[:1].get()
                        u.userID = data["user"]['id_str']#Should be uniqueId!!! Set as a qunique index
                        u.userName = data["user"]["screen_name"]
                        u.followersCount = data["user"]["followers_count"]
                        u.friendsCount = data["user"]["friends_count"]
                        u.retweetCount = data["retweet_count"]
                        u.isGeoEnabled = data["user"]['geo_enabled']
                        u.language = data["user"]['lang']
                        print "User!!!!",u.userName

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
                        t.tweetID=data["id"]
                        t.language = data["lang"]
                        t.text = data['text']
                        #t.createdAt = data["created_at"]
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
                        t.cleaned_text = cleanTweet(t)
                        t.save()
                        createdAt=datetime.datetime.strptime(str(data["created_at"]).replace(str(data["created_at"])[data["created_at"].index("+"):len(data["created_at"])-4],''),'%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone('UTC'))

                        tn=TweetNode.objects.create(objectID=str(t._object_key),tweetID=data["id"],in_reply_to_status_id=data["in_reply_to_status_id"],createdAt=createdAt)
                        if data["in_reply_to_status_id"]!=None:
                            t.calculate_Sentiment_Scores()
                            print t.pos_Score
                            print t.obj_Score
                            print t.neg_Score
                        if tn.in_reply_to_status_id!=None:
                            qs=TweetNode.objects.filter(tweetID=tn.in_reply_to_status_id)
                            if len(qs[:])>0:
                                parent_tn=qs[:1].get()
                                parent_tn.retweets.add(tn) if t.isRetweeted else parent_tn.replies.add(tn)
                                parent_tn.save()
                    else:
                        print "Tweet exists in the system"
                except Exception:
                    print Exception.message
        def on_error(self, status_code, data):
            print status_code
    stream = SubscriberUserStreamer(consumer_key, consumer_secret,access_token,access_token_secret)
    #registry=TwitterRegistry.objects.all()
    #twitterAccounts=registry.values_list('twitterUserName',flat=True)
    subscribers=Subscriber.objects.all()
    twitterAccounts=list(itertools.chain(*(subs.twitterusers.all() for subs in subscribers)))
    comma_sep_list=""
    for i,user in enumerate(twitterAccounts):
        comma_sep_list+=user.userID+", " if i<len(twitterAccounts)-1 else user.userID
    print(comma_sep_list)
    #stream.statuses.filter(follow=["Ford","Forduk","FordAutoShows","FordEu"])
    #stream.statuses.filter(locations=[-74.2591,40.4774,-73.7002,40.9176])
    stream.statuses.filter(follow=comma_sep_list,replies=all,language="en")
    #stream.statuses.filter(replies=all,language="en")
    #stream.statuses.filter(locations=[-74.2591,40.4774,-73.7002,40.9176])
    #stream.statuses.filter(follow=["Ford","Forduk","FordAutoShows","FordEu"],replies=all,language="en")
    #stream.statuses.filter(follow=["Ford","VW","Volkswagen","Forduk","FordAutoShows","FordEu","Toyota"])
    #Enable Count in IBM server
    #stream.statuses.filter(count=50000)
@celery_app.task()
def exec_Twitter_HashTag_Streamer():
    class HashTagStreamer(TwythonStreamer):
        def on_success(self, data):
            if 'text' in data:
                print(data)
                print(data['text'].encode('utf-8'))
                try:
                    authenticate(username='default', password='defaultpassword')
                    t_qs=Tweet.objects.filter(tweetID=data["id"])
                    if len(t_qs[:])==0:
                        qs=TwitterUser.objects.filter(userID=data["user"]["id_str"])
                        u = TwitterUser()
                        if len(qs[:])>0:
                            u=qs[:1].get()
                        u.userID = data["user"]['id_str']#Should be uniqueId!!! Set as a qunique index
                        u.userName = data["user"]["screen_name"]
                        u.followersCount = data["user"]["followers_count"]
                        u.friendsCount = data["user"]["friends_count"]
                        u.retweetCount = data["retweet_count"]
                        u.isGeoEnabled = data["user"]['geo_enabled']
                        u.language = data["user"]['lang']
                        print "User!!!!",u.userName

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
                        t.tweetID=data["id"]
                        t.language = data["lang"]
                        t.text = data['text']
                        #t.createdAt = data["created_at"]
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
                        t.cleaned_text = cleanTweet(t)
                        t.save()
                        createdAt=datetime.datetime.strptime(str(data["created_at"]).replace(str(data["created_at"])[data["created_at"].index("+"):len(data["created_at"])-4],''),'%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone('UTC'))

                        tn=TweetNode.objects.create(objectID=str(t._object_key),tweetID=data["id"],in_reply_to_status_id=data["in_reply_to_status_id"],createdAt=createdAt)
                        extractHashtags(data,tn,u)
                        if data["in_reply_to_status_id"]!=None:
                            t.calculate_Sentiment_Scores()
                            print t.pos_Score
                            print t.obj_Score
                            print t.neg_Score
                        if tn.in_reply_to_status_id!=None:
                            qs=TweetNode.objects.filter(tweetID=tn.in_reply_to_status_id)
                            if len(qs[:])>0:
                                parent_tn=qs[:1].get()
                                parent_tn.retweets.add(tn) if t.isRetweeted else parent_tn.replies.add(tn)
                                parent_tn.save()
                    else:
                        print "Tweet exists in the system"
                except Exception:
                    print Exception.message
        def on_error(self, status_code, data):
            print status_code
    stream = HashTagStreamer(consumer_key, consumer_secret,access_token,access_token_secret)
    hashtag_objs=HashTag.objects.all()
    if len(hashtag_objs[:])>0:
        #hastags=HashTag.objects.values_list('tag',flat=True)
        comma_sep_list=""
        for i,obj in enumerate(hashtag_objs):
            comma_sep_list+=obj.tag+", " if i<hashtag_objs.count()-1 else obj.tag
        print(comma_sep_list)

        stream.statuses.filter(track=comma_sep_list,replies=all,language="en")
import itertools
@celery_app.task()
def exec_Subscriber_Timeline_API():
    subscribers=Subscriber.objects.all()
    twitter_users=list(itertools.chain(*(subs.twitterusers.all() for subs in subscribers)))
    twitter = Twython(consumer_key, consumer_secret,access_token,access_token_secret)

    for user in twitter_users:
        print user.userName,"!!!"
        user_data=None
        try:
            user_data=twitter.show_user(screen_name=user.userName,include_entities=True)
            print user_data
            user.userID = user_data['id_str']
            user.userName = user_data["screen_name"]
            user.followersCount = user_data["followers_count"]
            user.friendsCount = user_data["friends_count"]
            user.retweetCount = user_data["status"]["retweet_count"]
            user.favouriteCount= user_data["status"]["favorite_count"]
            user.isGeoEnabled = user_data['geo_enabled']
            user.language = user_data['lang']
            user.save()
            print "test",user.userName
            try:
                user_timeline=twitter.get_user_timeline(user_id=long(user.userID),count=200,exclude_replies=0,include_rts=1)
                for tweet_data in user_timeline:
                    print  tweet_data
                    u=createTweetUser(tweet_data)
                    print "done",u.userID
                    t=createTweet(tweet_data)
                    buildAssociation(tweet_data,t,u)
            except TwythonError as e:
                print e
        except TwythonError as e:
            print e
        #api_url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
        #constructed_url = twitter.construct_api_url(api_url, user_id=user.userName,count=200,exclude_replies=0,include_rts=1)
def exec_Subscriber_Followers_API():
    subscribers=Subscriber.objects.all()
    twitter_users=list(itertools.chain(*(subs.twitterusers.all() for subs in subscribers)))
    twitter = Twython(consumer_key, consumer_secret,access_token,access_token_secret)

    for i,user in enumerate(twitter_users):
        print user.userName,"!!!"
        if (i+1)%15==0:
            print "Waiting 15 minutes for the next call"
            sleep(910)
        try:
            print "!!!TIME FOR FOLLOWERS!!!"
            followers=twitter.get_followers_list(screen_name=user.userName,include_user_entities=True,count=200)
            for f in followers:
                print f
        except TwythonError as e:
            print e

import HTMLParser
html_parser=HTMLParser.HTMLParser()
import re
def cleanTweet(t):
    text=html_parser.unescape(t.text)
    text=re.sub(r"http\S+", "", text)
    text=re.sub(r"ftp\S+", "", text)
    urls=[str(ur['url']) for ur in t.urls]
    text=text.encode('ascii','ignore')
    for word in text.split():
        if word.startswith("@") or word in urls or word.startswith("#"):
            text=text.replace(word,"")
    print text
    #text=text.lower()
    return text
def createTweetUser(data):
    print data["user"]["id_str"]
    qs=TwitterUser.objects.filter(userID=data["user"]["id_str"])
    #print qs[0]
    u = TwitterUser()
    if len(qs[:])>0:
        u=qs[0]
    u.userID = data["user"]['id_str']
    u.userName = data["user"]["name"]
    u.followersCount = data["user"]["followers_count"]
    u.friendsCount = data["user"]["friends_count"]
    u.retweetCount = data["retweet_count"]
    u.isGeoEnabled = data["user"]['geo_enabled']
    u.language = data["user"]['lang']
    u.save()
    return u
def createTweet(data):
    print "start"
    t=Tweet()
    if data["place"]!=None:
        print "There is place"
        coord=data["place"]["bounding_box"]['coordinates'][0]
        if coord[0][0]==coord[1][0] and coord[0][1]==coord[1][1]:
            t.geopoint = coord[0];print "geom trick"
        else:
            t.geometry=[[coord[0],coord[1],coord[2],coord[3],coord[0]]]
        if data["geo"]!=None:
            t.geopoint = data["geo"]["coordinates"]
        t.tweetID=data["id"]
        t.placeId = data["place"]["id"]
        t.placeFullName = data["place"]["full_name"]
        t.placeName = data["place"]["name"]
        t.countryCode = data["place"]["country_code"]
        t.placeType = data["place"]["place_type"]
    t.language = data["lang"]
    t.text = data['text']
    #t.createdAt = data["created_at"]
    #t.timestamp = datetime.datetime.fromtimestamp(long(data["timestamp_ms"])/1e3)
    t.isRetweeted = data["retweeted"]
    t.isFavorited= data["favorited"]
    t.favoriteCount = data["favorite_count"]
    t.retweetCount = data["retweet_count"]
    #t.trends = data["entities"]["trends"]
    t.symbols = data["entities"]["symbols"]
    t.urls = data["entities"]["urls"]
    t.cleaned_text = cleanTweet(t)
    t.save()
    return t
def buildAssociation(data,t,u):
    createdAt=datetime.datetime.strptime(str(data["created_at"]).replace(str(data["created_at"])[data["created_at"].index("+"):len(data["created_at"])-4],''),'%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone('UTC'))
    tn=TweetNode.objects.create(objectID=str(t._object_key),tweetID=data["id"],in_reply_to_status_id=data["in_reply_to_status_id"],createdAt=createdAt)

    extractHashtags(data,tn,u)
    if data["in_reply_to_status_id"]!=None:
        t.calculate_Sentiment_Scores()
        print t.pos_Score
        print t.obj_Score
        print t.neg_Score
    if tn.in_reply_to_status_id!=None:
        qs=TweetNode.objects.filter(tweetID=tn.in_reply_to_status_id)
        if len(qs[:])>0:
            parent_tn=qs[:1].get()
            parent_tn.retweets.add(tn) if t.isRetweeted else parent_tn.replies.add(tn)
            parent_tn.save()

def extractHashtags(data,tn,u):
    for word in [x["text"] for x in data["entities"]["hashtags"]]:
        qs=HashTag.objects.filter(tag=word)
        hash_tag=None
        if len(qs[:])>0:
            hash_tag=qs[0]
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

