__author__ = 'anil'
from socialapp.models import *
import itertools
import numpy as np
from socialapp.api import *
def calculateTopHashtags(tns,user_hashtags,n):
    hashtag_count_list=sorted(list(np.unique(np.array([{"tag":t.tag,"count":tns.filter(hashtags__tag=t.tag).count()} for t in user_hashtags]))),key=lambda x:x['count'],reverse=True)
    print hashtag_count_list
    return hashtag_count_list[:n] if n<len(hashtag_count_list) else hashtag_count_list

def calculateHashtagsByLocation(tns,user_hashtags):
    hashtag_country_list=sorted(list(np.unique(np.array([{"tag":h.tag,"countryCode":Tweet.objects.filter(_id=t.objectID).values_list("countryCode"),"tweetID":t.tweetID} for h in user_hashtags for t in tns.filter(hashtags__tag=h.tag).all()]))))
    print hashtag_country_list
    return hashtag_country_list

def calculateKPIs(request,startDate,endDate):
    s=Subscriber.objects.filter(name=request.session["username"])[0]
    print s.name
    twitter_users=s.twitterusers.all() #can be a broadcast variable
    user_hashtags=list(itertools.chain(*(user.hashtags.all() for user in twitter_users))) #can be a broadcast variable too
    tns=TweetNode.objects.filter(createdAt__range=[startDate,endDate]) #can be rdd
    #calculateHashtagsByLocation(tns,user_hashtags)
    [HashtagBenchmark(subscriber=request.session["username"],hashtag=t["tag"],count=t["count"]).save() for t in calculateTopHashtags(tns,user_hashtags,5)]