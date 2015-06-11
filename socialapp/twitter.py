__author__ = 'root'

####################################################################
consumer_key="Vs7V2k4vPWMMyTFqLzqPkM6wE"
consumer_secret="aWNRzh74LUT1fuW35y6VzRDtvuimQ4LjFGMnMMkEXI0Y9LSpkf"

access_token="258113369-63Y2Cqr9q0Bo02WU4AS8Bjiv3JnHP2Us7HimK26G"
access_token_secret="Z4Sf9EyLbOJ4jPI5WlZPZUyv3OwluuZXiKXn0pamk8Dly"
###################################################################
def exec_Twitter_Streamer():
    from twython import TwythonStreamer
    from socialapp.models import Tweet,TwitterUser,BoundingBox,TweetNode
    import configparser
    config = configparser.ConfigParser()
    config.read('../app.conf')
    from django.contrib.auth import authenticate
    import datetime
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
                t.hashtags = data["entities"]["hashtags"]
                t.symbols = data["entities"]["symbols"]
                t.urls = data["entities"]["urls"]
                t.save()
                """if data["in_reply_to_status_id"]!=None:
                    t.calculate_Sentiment_Scores()
                    print t.pos_Score
                    print t.obj_Score
                    print t.neg_Score"""
                tn=TweetNode.objects.create(objectID=str(t._object_key),tweetID=data["id"],in_reply_to_status_id=data["in_reply_to_status_id"])
                u.tweets.add(tn)
                u.save()
                if tn.in_reply_to_status_id!=None:
                    qs=TweetNode.objects.filter(tweetID=tn.in_reply_to_status_id)
                    if len(qs[:])>0:
                        parent_tn=qs[:1].get()
                        parent_tn.replies.add(tn)
                        parent_tn.save()

    stream = MyStreamer(consumer_key, consumer_secret,access_token,access_token_secret)


    stream.statuses.filter(locations=[-74.2591,40.4774,-73.7002,40.9176])
    stream.statuses.filter(replies=all)
    stream.statuses.filter(language="en")
    #stream.statuses.filter(follow=["Ford","VW","Volkswagen","Forduk","FordAutoShows","FordEu","Toyota"])
    #Enable Count in IBM server
    #stream.statuses.filter(count=50000)


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

