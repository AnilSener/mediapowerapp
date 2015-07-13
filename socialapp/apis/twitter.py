__author__ = 'root'
from twython import TwythonStreamer,Twython,TwythonError
from socialapp.models import *
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
        global stopwords
        def __init__(self):
            stopwordstextfile= open(os.path.join(settings.BASE_DIR,'socialapp/apis/files/stopwords.txt'), 'r')
            stopwords = [w.replace('\n','') for w in stopwordstextfile.readlines()]
            stopwordstextfile.close()
        def on_success(self, data):
            if 'text' in data:
                print(data)
                print(data['text'].encode('utf-8'))
                try:
                    authenticate(username='default', password='defaultpassword')
                    t_qs=Tweet.objects.filter(tweetID=str(data["id_str"]))
                    if len(t_qs[:])==0:
                        qs=TwitterUser.objects.filter(userID=data["user"]["id_str"])
                        u = TwitterUser()
                        if len(qs[:])>0:
                            u=qs[:1].get()
                        u.userID = str(data["user"]['id_str'])#Should be uniqueId!!! Set as a qunique index
                        u.userName = str(data["user"]["screen_name"])
                        u.followersCount = data["user"]["followers_count"]
                        u.friendsCount = data["user"]["friends_count"]
                        u.retweetCount = data["retweet_count"]
                        u.isGeoEnabled = data["user"]['geo_enabled']
                        u.language = data["user"]['lang']
                        print "User!!!!",u.userName

                        t=Tweet()
                        t.tweetID=str(data["id_str"])
                        t.language = data["lang"]
                        t.text = data['text']
                        t.timestamp = datetime.datetime.fromtimestamp(long(data["timestamp_ms"])/1e3)
                        t.isRetweeted = data["retweeted"]
                        t.isFavorited= data["favorited"]
                        t.favoriteCount = data["favorite_count"]
                        t.retweetCount = data["retweet_count"]
                        t.trends = data["entities"]["trends"]
                        t.symbols = data["entities"]["symbols"]
                        t.urls = data["entities"]["urls"]
                        t.cleaned_text = cleanTweet(t,stopwords)
                        t.save()
                        p=createPlace(data["place"],data["geo"],t.tweetID)
                        """if p!=None:
                            updated = Tweet.objects(pk=t.tweetID).update_one(set__location=p)
                            if not updated:
                                print "location not updated" """
                        createdAt=datetime.datetime.strptime(str(data["created_at"]).replace(str(data["created_at"])[data["created_at"].index("+"):len(data["created_at"])-4],''),'%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone('UTC'))

                        tn=TweetNode.objects.create(tweetID=str(data["id_str"]),in_reply_to_status_id=str(data["in_reply_to_status_id"]),createdAt=createdAt)
                        if data["in_reply_to_status_id"]!=None:
                            t.calculate_Sentiment_Scores()
                            print t.pos_Score
                            print t.obj_Score
                            print t.neg_Score
                        if tn.in_reply_to_status_id!=None and t.language=="en":
                            qs=TweetNode.objects.filter(tweetID=str(tn.in_reply_to_status_id))
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
    subscribers=Subscriber.objects.all()
    twitterAccounts=list(itertools.chain(*(subs.twitterusers.all() for subs in subscribers)))
    comma_sep_list=""
    for i,user in enumerate(twitterAccounts):
        comma_sep_list+=user.userID+", " if i<len(twitterAccounts)-1 else user.userID
    print(comma_sep_list)

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
        global stopwords
        def __init__(self):
            stopwordstextfile= open(os.path.join(settings.BASE_DIR,'socialapp/apis/files/stopwords.txt'), 'r')
            stopwords = [w.replace('\n','') for w in stopwordstextfile.readlines()]
            stopwordstextfile.close()
        def on_success(self, data):
            if 'text' in data:
                print(data)
                print(data['text'].encode('utf-8'))
                try:
                    authenticate(username='default', password='defaultpassword')
                    t_qs=Tweet.objects.filter(tweetID=str(data["id_str"]))
                    if len(t_qs[:])==0:
                        qs=TwitterUser.objects.filter(userID=str(data["user"]["id_str"]))
                        u = TwitterUser()
                        if len(qs[:])>0:
                            u=qs[:1].get()
                        u.userID = str(data["user"]['id_str'])#Should be uniqueId!!! Set as a qunique index
                        u.userName = str(data["user"]["screen_name"])
                        u.followersCount = data["user"]["followers_count"]
                        u.friendsCount = data["user"]["friends_count"]
                        u.retweetCount = data["retweet_count"]
                        u.isGeoEnabled = data["user"]['geo_enabled']
                        u.language = data["user"]['lang']
                        print "User!!!!",u.userName

                        t=Tweet()
                        t.tweetID=str(data["id_str"])
                        t.language = data["lang"]
                        t.text = data['text']
                        t.timestamp = datetime.datetime.fromtimestamp(long(data["timestamp_ms"])/1e3)
                        t.isRetweeted = data["retweeted"]
                        t.isFavorited= data["favorited"]
                        t.favoriteCount = data["favorite_count"]
                        t.retweetCount = data["retweet_count"]
                        t.trends = data["entities"]["trends"]
                        t.symbols = data["entities"]["symbols"]
                        t.urls = data["entities"]["urls"]
                        t.cleaned_text = cleanTweet(t,stopwords)
                        t.save()
                        p=createPlace(data["place"],data["geo"],t.tweetID)
                        """if p!=None:
                            updated = Tweet.objects(pk=t.tweetID).update_one(set__location=p)
                            if not updated:
                                print "location not updated"""""
                        createdAt=datetime.datetime.strptime(str(data["created_at"]).replace(str(data["created_at"])[data["created_at"].index("+"):len(data["created_at"])-4],''),'%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone('UTC'))

                        tn=TweetNode.objects.create(tweetID=str(data["id_str"]),in_reply_to_status_id=str(data["in_reply_to_status_id"]),createdAt=createdAt)
                        extractHashtags(data,tn,u)
                        if data["in_reply_to_status_id"]!=None and t.language=="en":
                            t.calculate_Sentiment_Scores()
                            print t.pos_Score
                            print t.obj_Score
                            print t.neg_Score
                        if tn.in_reply_to_status_id!=None:
                            qs=TweetNode.objects.filter(tweetID=str(tn.in_reply_to_status_id))
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
#Twitter Rest API Connection
twitter = Twython(consumer_key, consumer_secret,access_token,access_token_secret)

@celery_app.task()
def exec_Subscriber_Timeline_API():
    subscribers=Subscriber.objects.all()
    #subscribers=Subscriber.objects.filter(name="Ford").all()
    twitter_users=[u for subs in subscribers for u in subs.twitterusers.all()]
    stopwordstextfile= open(os.path.join(settings.BASE_DIR,'socialapp/apis/files/stopwords.txt'), 'r')
    stopwords = [w.replace('\n','') for w in stopwordstextfile.readlines()]
    stopwordstextfile.close()
    for user in twitter_users:
        print user.userName,"!!!"
        user_data=None
        try:
            sleep(20)
            user_data=twitter.show_user(screen_name=user.userName,include_entities=True)
            print user_data
            user.userID = str(user_data['id_str'])
            user.userName = str(user_data["screen_name"])
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
                    qs=Tweet.objects.filter(pk=str(tweet_data["id_str"]))
                    if len(qs[:])>0:
                        print "Tweet available in the system"
                        pass
                    u=createTweetUser(tweet_data)
                    print "done",u.userID
                    t,p=createTweet(tweet_data,stopwords)
                    buildAssociation(tweet_data,t,u,p)
            except TwythonError as e:
                print e.message
        except TwythonError as e:
            print e.message
        #api_url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
        #constructed_url = twitter.construct_api_url(api_url, user_id=user.userName,count=200,exclude_replies=0,include_rts=1)
@celery_app.task()
def exec_Subscriber_Followers_API():
    subscribers=Subscriber.objects.all()
    twitter_users=list(itertools.chain(*(subs.twitterusers.all() for subs in subscribers)))
    for i,user in enumerate(twitter_users):
        print user.userName,"!!!"
        user_data=twitter.show_user(screen_name=user.userName,include_entities=True)
        print user_data
        user.userID = str(user_data['id_str'])
        user.userName = str(user_data["screen_name"])
        user.followersCount = user_data["followers_count"]
        user.friendsCount = user_data["friends_count"]
        user.retweetCount = user_data["status"]["retweet_count"]
        user.favouriteCount= user_data["status"]["favorite_count"]
        user.isGeoEnabled = user_data['geo_enabled']
        user.language = user_data['lang']
        user.save()
        """if (i+1)%10==0:
            print "Waiting 15 minutes for the next call"
            sleep(910)"""
        try:
            print "!!!TIME FOR FOLLOWERS!!!"
            sleep(120)
            followerIDs=twitter.get_followers_ids(screen_name = user)#.get_followers_list(screen_name=user.userName,include_user_entities=True,count=200)
            for x in followerIDs["ids"]:
                fdata = twitter.show_user(user_id=x)
                print "follower",fdata
                f=createFollowerUser(fdata)
                user.followers.add(f)
            user.save()
        except TwythonError as e:
            print e.message


import HTMLParser
html_parser=HTMLParser.HTMLParser()
import re
import os
from django.conf import settings
def cleanTweet(t,stopwords):
    text=html_parser.unescape(t.text)
    text=re.sub(r"http\S+", "", text)
    text=re.sub(r"ftp\S+", "", text)
    urls=[str(ur['url']) for ur in t.urls]
    text=text.encode('ascii','ignore')
    for word in text.split():
        if word.startswith("@") or word in urls or word.startswith("#") or word in stopwords:
            text=text.replace(word,"")
    print text
    return text
def createTweetUser(data):
    print data["user"]["id_str"]
    qs=TwitterUser.objects.filter(userID=str(data["user"]["id_str"]))
    #print qs[0]
    u = TwitterUser()
    if len(qs[:])>0:
        u=qs[0]
    u.userID = str(data["user"]['id_str'])
    u.userName = str(data["user"]["screen_name"])
    u.followersCount = data["user"]["followers_count"]
    u.friendsCount = data["user"]["friends_count"]
    u.retweetCount = data["retweet_count"]
    u.isGeoEnabled = data["user"]['geo_enabled']
    u.language = data["user"]['lang']
    u.save()
    return u
def createFollowerUser(data):
    print data["id_str"]
    qs=TwitterUser.objects.filter(userID=str(data["id_str"]))
    #print qs[0]
    u = TwitterUser()
    if len(qs[:])>0:
        u=qs[0]
    u.userID = str(data['id_str'])
    u.userName = str(data["screen_name"])
    u.followersCount = data["followers_count"]
    u.friendsCount = data["friends_count"]
    u.retweetCount = data["retweet_count"] if "retweet_count" in data else 0
    u.isGeoEnabled = data['geo_enabled']
    u.language = data['lang']
    if data['geo_enabled']==True:
        print "Fiels available"
        p=createPlace(data['status']['place'],data['status']['geo'],None,data['location'])
        if p!=None:
            pn=createPlaceNode(p)
            u.locations.add(pn)
    u.save()

    return u
def createTweet(data,stopwords):
    print "start"
    t=Tweet()
    t.tweetID=str(data["id_str"])
    t.language = data["lang"]
    t.text = data['text']
    t.isRetweeted = data["retweeted"]
    t.isFavorited= data["favorited"]
    t.favoriteCount = data["favorite_count"]
    t.retweetCount = data["retweet_count"]
    t.symbols = data["entities"]["symbols"]
    t.urls = data["entities"]["urls"]
    t.cleaned_text = cleanTweet(t,stopwords)
    t.save()
    p=None
    if data["user"]['geo_enabled']==True:
        p=createPlace(data["place"],data["geo"],t.tweetID,data['user']['location'])
    """if p!=None:
        updated = Tweet.objects(pk=t.tweetID).update_one(set__location=p)
        if not updated:
            print "location not updated" """
    return t,p
def buildAssociation(data,t,u,pObj=None):
    createdAt=datetime.datetime.strptime(str(data["created_at"]).replace(str(data["created_at"])[data["created_at"].index("+"):len(data["created_at"])-4],''),'%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone('UTC'))
    tn=TweetNode.objects.create(tweetID=str(data["id_str"]),in_reply_to_status_id=str(data["in_reply_to_status_id"]),createdAt=createdAt)
    if pObj!=None:
        pn=createPlaceNode(pObj)
        tn.places.add(pn)
        tn.save()
    extractHashtags(data,tn,u)
    if data["in_reply_to_status_id"]!=None and t.language=="en":
        t.calculate_Sentiment_Scores()
        print t.pos_Score
        print t.obj_Score
        print t.neg_Score
    if tn.in_reply_to_status_id!=None:
        qs=TweetNode.objects.filter(tweetID=str(tn.in_reply_to_status_id))
        if len(qs[:])>0:
            parent_tn=qs[:1].get()
            parent_tn.retweets.add(tn) if t.isRetweeted else parent_tn.replies.add(tn)
            parent_tn.save()

def extractHashtags(data,tn,u):
    try:
        if data["entities"]["hashtags"]!=None:
            for word in [x["text"] for x in data["entities"]["hashtags"]]:
                word=word.encode('ascii','ignore')
                qs=HashTag.objects.filter(tag=word)
                hash_tag=None
                if len(qs[:])>0:
                    hash_tag=qs[0]
                else:
                    hash_tag=HashTag.objects.create(tag=word)
                tn.hashtags.add(hash_tag)

                previous_user_tags=[obj.tag for obj in list(u.hashtags.all())]
                print "previous hashtags",previous_user_tags
                if not word in previous_user_tags:
                    u.tweets.add(tn)
                    u.hashtags.add(hash_tag)
            tn.save()
            u.save()
            print u.hashtags.all()
    except Exception as e:
        print e.message

def createPlaceNode(placeObj):
    pn=None
    if placeObj!=None:
        try:
            print "There is place"
            qs=PlaceNode.objects.filter(placeId=placeObj.placeId)
            pn=PlaceNode()
            if len(qs[:])>0:
                print "Place Node exists"
                pn=qs[0]
            else:
                qs=PlaceNode.objects.filter(location=placeObj.location)
                if len(qs[:])>0:
                    print "Place Document with location info exists"
                    pn=qs[0]
            if placeObj.country!=None:
                pn.placeId = placeObj.placeId
                pn.placeFullName = placeObj.placeFullName
                pn.placeName = placeObj.placeName
                pn.country = placeObj.country
                pn.countryCode = placeObj.countryCode
                pn.placeType = placeObj.placeType
                pn.save()
                print "Place Node with ID",pn.placeId," and name ",pn.placeName
            elif  placeObj.location!=None:
                pn.location=placeObj.location
                pn.save()
                print "Place Node with Location ",pn.location

        except Exception as e:
            print e
    return pn
def createPlace(place,geo,tweetID=None,location=None):
    p=None
    if place!=None:
        try:
            print "There is place"
            qs=Place.objects.filter(placeId=str(place["id"]))
            p=Place()
            if location!=None:
                location=location.encode('ascii','ignore')
            if len(qs[:])>0:
                print "Place Document exists"
                p=qs[0]
            else:
                qs=Place.objects.filter(location=str(location))
                if len(qs[:])>0:
                    print "Place Document with location info exists"
                    p=qs[0]
            coord=place["bounding_box"]['coordinates'][0]
            if coord[0][0]==coord[1][0] and coord[0][1]==coord[1][1]:
                p.geopoint = coord[0];print "geom trick"
            else:
                p.geometry=[[coord[0],coord[1],coord[2],coord[3],coord[0]]]
            if geo!=None:
                p.geopoint = geo["coordinates"]
            if place["country"]!=None:
                p.placeId = str(place["id"])
                p.placeFullName = str(place["full_name"].encode('ascii','ignore')) if place["full_name"]!=None else ""
                p.placeName = str(place["name"].encode('ascii','ignore')) if place["name"]!=None else ""
                p.country = str(place["country"].encode('ascii','ignore'))
                p.countryCode = str(place["country_code"])
                p.placeType = str(place["place_type"].encode('ascii','ignore'))
            elif location!=None:
                p.location = str(location)
            if tweetID!=None:
                p.tweetID=tweetID
            p.save()
        except Exception as e:
            print e
    return p
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

