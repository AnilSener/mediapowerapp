__author__ = 'anil'
from socialapp.models import *
import itertools
import numpy as np
from socialapp.api import *
from socialapp.util import week_of_month
def calculateTopHashtags(tns,user_hashtags,n):
    hashtag_count_list=sorted(list(np.unique(np.array([{"tag":t.tag,"count":tns.filter(hashtags__tag=t.tag).count()} for t in user_hashtags]))),key=lambda x:x['count'],reverse=True)
    print hashtag_count_list
    #return hashtag_count_list[:n] if n<len(hashtag_count_list) else hashtag_count_list
    return hashtag_count_list
"""def calculateHashtagsByLocation(tn,user_hashtags):
    hashtag_country_list=sorted(list(np.unique(np.array([{"tag":h.tag,"countryCode":Tweet.objects.filter(_id=tn.objectID).values_list("countryCode"),"tweetID":tn.tweetID}]))))
    print hashtag_country_list
    return hashtag_country_list"""

def calculateKPIs(request,startDate,endDate):
    s=Subscriber.objects.filter(name=request.session["username"])[0]
    N=5
    from pyspark import SparkConf,SparkContext
    from pyspark.sql import Row
    conf = (SparkConf()
    #.setMaster("yarn-client")
    .setMaster("local")
    #you can shift between local and yarn-client mode, it is very important to have same python2.7 version in all servers
    .setAppName("forecastingengine")
    .set("spark.executor.memory", "512m")
    .set("spark.driver.memory", "512m")
    .set("spark.python.worker.memory", "4g") #My environment didnt support more please increase to 8gb
    .set("spark.shuffle.memoryFraction", 0.4)
    .set("spark.default.parallelism",2) #I am using only 2 nodes for execution
    .set("spark.executor.instances", 2)
    .set("spark.executor.cores", 2) #My environment didnt support more please increase to 4 cores
    )
    sc = SparkContext(conf=conf)
    print s.name
    twitter_users=s.twitterusers.all() #can be a broadcast variable
    print twitter_users
    userHashtagsBroadcast=sc.broadcast(list(itertools.chain(*([h.tag for h in user.hashtags.all()] for user in twitter_users)))) #can be a broadcast variable too
    print userHashtagsBroadcast.value
    #print TweetNode.objects.all()
    tnsRDD=sc.parallelize(list(TweetNode.objects.all()),2).cache()#.filter(createdAt__range=[startDate,endDate]) #can be rdd
    """
    #calculateHashtagsByLocation(tns,user_hashtags)"""
    #[HashtagBenchmark(subscriber=request.session["username"],hashtag=t["tag"],count=t["count"]).save() for t in calculateTopHashtags(tns,user_hashtags,5)]
    #hashtagCountRDD=user_hashtags.map(lambda h: (h.tag,sum(1 if h in n.hashtags.all() else 0 for n in tns.value )))
    """.filter(lambda tn:tn.createdAt>=startDate and tn.createdAt<=endDate)"""
    tweetHashtagsRDD=tnsRDD.map(lambda tn:(tn,[t.tag for t in tn.hashtags.all()])).filter(lambda (tn,taglist):len(taglist)>0)
    flattedTweetHashtagsRDD=tweetHashtagsRDD.flatMapValues(lambda x:x).filter(lambda (tn,tag):tag in userHashtagsBroadcast.value).cache()
    hashtagCounts=flattedTweetHashtagsRDD.countByValue().items()
    #print flattedTweetHashtagsRDD.take(10)
    sortedHashtagCounts=sorted(hashtagCounts,key=lambda x:x[1],reverse=True)
    topHashtagCounts=sortedHashtagCounts[:N] if N<len(sortedHashtagCounts) else sortedHashtagCounts
    [HashtagBenchmark(subscriber=request.session["username"],hashtag=t[0][1],count=t[1]).save() for t in topHashtagCounts]
    countryCodeHashtagsRDD=flattedTweetHashtagsRDD.map(lambda (tn,tag):(Row(countryCode=Tweet.objects.filter(pk=tn.tweetID).values_list("location__countryCode"),created=tn.createdAt,tag=tag)))
    if (endDate.year-startDate.year)>1:
        groupedRDD=countryCodeHashtagsRDD.groupBy(lambda record:(record.created.year,record.created.month,record.tag))
    elif endDate.year==startDate.year and (endDate.month-endDate.month)>1:
        groupedRDD=countryCodeHashtagsRDD.groupBy(lambda record:(record.created.month,record.tag))
    elif endDate.year==startDate.year and (endDate.month-endDate.month)>=1:
        groupedRDD=countryCodeHashtagsRDD.groupBy(lambda record:(week_of_month(record.created),record.tag))
    else:
        groupedRDD=countryCodeHashtagsRDD.groupBy(lambda record:(record.created.day,record.tag))

    countryCodeHashtagCounts=groupedRDD.mapValues(len)
    print countryCodeHashtagCounts.collect()
    #print hashtagCountRDD.collect()

