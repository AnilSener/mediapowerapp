__author__ = 'anil'
from socialapp.models import *
import itertools
import numpy as np
from socialapp.api import *
from socialapp.util import week_of_month
import datetime
import math
from pytz import timezone

def calculateKPIs(request,tMode,startDate,endDate):
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
    creationdate=datetime.datetime.now().replace(tzinfo=timezone('UTC'))
    subscriber_twitter_users=s.twitterusers.all() #can be a broadcast variable
    subscriber_user_count=len(subscriber_twitter_users)
    subscribers_count=len(Subscriber.objects.all())
    all_twitter_users=sc.broadcast([(s,user) for s in Subscriber.objects.all() for user in s.twitterusers.all()])

    #Follower KPI calculations
    #########################################
    allFollowersRDD=sc.parallelize([(str(s.name),[(l.countryCode,Place.objects.filter(placeId=l.placeId).get(),f.userID) for l in f.locations.all()]) for (s,user) in all_twitter_users.value for f in user.followers.all()],2)
    pipelinedFollowerRDD=allFollowersRDD.filter(lambda (x,y):len(y)>0).map(lambda (x,y):Row(subscriber=x,countryCode=y[0][0],geopoint=y[0][1].geopoint,geometry=y[0][1].geometry['coordinates'],placeFullName=y[0][1].placeFullName,followerID=y[0][2])).filter(lambda record: record.subscriber=="Ford").cache()
    #print "Followers",pipelinedFollowerRDD.collect()
    countryGroupedCountRDD=pipelinedFollowerRDD.map(lambda record:(record.countryCode,1)).reduceByKey(lambda a,b:a+b)
    [CountryFollower(creationdate=creationdate,subscriber=request.session["username"],code=str(code),count=count).save() for (code,count) in countryGroupedCountRDD.collect()]
    geoGroupedCountRDD=pipelinedFollowerRDD.map(lambda record:(((record.geometry[0][0][0]+record.geometry[0][1][0])/2,(record.geometry[0][0][1]+record.geometry[0][2][1])/2,record.placeFullName),1)).reduceByKey(lambda a,b:a+b)
    print geoGroupedCountRDD.collect()
    [GeoFollower(creationdate=creationdate,subscriber=request.session["username"],geopointX=k[0],geopointY=k[1],placeName=k[2],count=count).save() for (k,count) in geoGroupedCountRDD.collect()]
    #"coordinates" : [ [ [ 32.692242, 39.8102322 ], [ 32.8538328, 39.8102322 ], [ 32.8538328, 39.9085469 ], [ 32.692242, 39.9085469 ], [ 32.692242, 39.8102322 ] ] ]

    pipelinedFollowerRDD.unpersist()
    ####################################

    #User KPI calculations:
    twitter_users=list((s.name,s.twitterusers.all()) for s in Subscriber.objects.all())
    user_count=sorted([(k,len(v)) for (k,v) in twitter_users],key=lambda (k,v):-v)
    rank=calculateRanking(request.session["username"],user_count)
    average_user_count=sum(v for (k,v) in user_count)/float(len(user_count))
    CompetitorBenchmark(KPI="No of Twitter Users",subscriber=request.session["username"],creationdate=creationdate,subscribervalue=subscriber_user_count,average=average_user_count,ranking=rank).save()

    #Hashtagy KPI calculations:
    subscriberHashtagsBroadcast=sc.broadcast(list(set(itertools.chain(*([h.tag for h in user.hashtags.all()] for user in subscriber_twitter_users))))) #can be a broadcast variable too
    print subscriberHashtagsBroadcast.value
    subscriber_hashtag_count=len(subscriberHashtagsBroadcast.value)
    all_hashtags=[(s.name,list(set([h.tag for user in s.twitterusers.all() for h in user.hashtags.all()]))) for s in Subscriber.objects.all()]
    all_hashtag_counts=sorted([(k,len(v)) for (k,v) in all_hashtags],key=lambda (k,v):-v)
    average_hashtag_count=sum(v for (k,v) in all_hashtag_counts)/float(len(all_hashtag_counts))
    rank=calculateRanking(request.session["username"],all_hashtag_counts)
    CompetitorBenchmark(KPI="No of Hashtags",subscriber=request.session["username"],creationdate=creationdate,subscribervalue=subscriber_hashtag_count,average=average_hashtag_count,ranking=rank).save()

    #Tweet Count KPIs
    ###################################################
    #,sum(t.replies.count() for t in user.tweets.all())
    x=reduce(lambda x,y:(x[0]+y[0],x[1]+y[1],x[2]+y[2],x[3]+y[3],x[4]+y[4]),[(user.tweets.count(),user.retweetCount,user.favouriteCount,user.followersCount,sum(f.followersCount for f in user.followers.all())) for user in subscriber_twitter_users])
    subscriberTweetCounts={"No of Tweets":x[0],"No of Retweets":x[1],"Favourites Count":x[2],"No of Followers":x[3],"No of 2nd Degree Connections":x[4]}
    print subscriberTweetCounts
    allCountsRDD=sc.parallelize([(str(s.name),(user.tweets.count(),user.retweetCount,user.favouriteCount,user.followersCount,sum(f.followersCount for f in user.followers.all()))) for (s,user) in all_twitter_users.value])
    #print allCountsRDD.collect()
    allTweetCounts=allCountsRDD.reduceByKeyLocally(lambda x,y:(x[0]+y[0],x[1]+y[1],x[2]+y[2],x[3]+y[3],x[4]+y[4])).items()
    i=0
    for k,v in subscriberTweetCounts.items():
        count_list=[]
        for j in range(subscribers_count):
            count_list.append((allTweetCounts[j][0],allTweetCounts[j][1][i]))
        sorted_count_list=sorted(count_list,key=lambda (k,v):-v)
        average_count=sum(v for (k,v) in sorted_count_list)/float(len(sorted_count_list))
        rank=calculateRanking(request.session["username"],sorted_count_list)
        CompetitorBenchmark(KPI=k,subscriber=request.session["username"],creationdate=creationdate,subscribervalue=v,average=average_count,ranking=rank).save()
        i+=1
    ##########################################


    #print TweetNode.objects.all()
    tnsRDD=sc.parallelize(list(TweetNode.objects.all()),2).filter(lambda tn:tn.createdAt>=startDate and tn.createdAt<=endDate).map(lambda tn:(tn,Tweet.objects.filter(pk=tn.tweetID).get())).cache()
    timeBasedRDD=tnsRDD.map(lambda (tn,tObj):(Row(created=tn.createdAt,subscriber=[str(s.name) for u in tn.owner.all() for s in u.account.all()],tnObj=tn,tweetObj=tObj))).filter(lambda record:len(record.subscriber)>0).cache()
    #Senitment Competition KPIs
    sentimentScoresPairedRDD=timeBasedRDD.filter(lambda record:record.tweetObj.obj_Score!=None).map(lambda record: (record.subscriber[0],(record.tweetObj.obj_Score,record.tweetObj.neg_Score,record.tweetObj.pos_Score,1)))
    allSubscribersScoresRDD=sentimentScoresPairedRDD.reduceByKey(lambda a,b:(a[0]+b[0],a[1]+b[1],a[2]+b[2],a[3]+b[3])).map(lambda (x,y):(x,(y[0]/float(y[3]),y[1]/float(y[3]),y[2]/float(y[3]))))
    #onlySubscribersScoresRDD=allSubscribersScoresRDD.filter(lambda (k,v):k==request.session["username"])
    #print "All Scores",allSubscribersScoresRDD.collect()
    #print sentimentScoresPairedRDD.filter(lambda (k,v):v=='Chevrolet').take(1)
    #print "time",timeBasedRDD.filter(lambda record:'Chevrolet' in record.subscriber).filter(lambda record:record.tweetObj.obj_Score!=None).take(1)
    allSubscribersScores=allSubscribersScoresRDD.collect()
    print allSubscribersScores

    onlySubscribersScores=None
    for (k,v) in allSubscribersScores:
        if k==str(request.session["username"]):
            onlySubscribersScores=v
    print onlySubscribersScores
    kpi_list=["Average Objective Sentiment","Average Negative Sentiment","Average Positive Sentiment"]
    for i,value in enumerate(onlySubscribersScores):
        count_list=[]
        for scores in allSubscribersScores:
            count_list.append((scores[0],scores[1][i]))
        sorted_count_list=sorted(count_list,key=lambda (k,v):-v)
        average_count=sum(v for (k,v) in sorted_count_list)/float(len(sorted_count_list))
        rank=calculateRanking(request.session["username"],sorted_count_list)
        CompetitorBenchmark(KPI=kpi_list[i],subscriber=request.session["username"],creationdate=creationdate,subscribervalue=value,average=average_count,ranking=rank).save()

    #print timeBasedRDD.take(1)
   #USER  HASHTAG BASED RDDs
    onlyHashtagTweetsRDD=tnsRDD.map(lambda (tn,tObj):((tn,tObj),[t.tag for t in tn.hashtags.all()])).filter(lambda ((tn,tObj),taglist):len(taglist)>0)
    flattedTweetHashtagsRDD=onlyHashtagTweetsRDD.flatMapValues(lambda x:x).filter(lambda ((tn,tObj),tag):tag in subscriberHashtagsBroadcast.value).cache()
    hashtagCounts=flattedTweetHashtagsRDD.map(lambda (k,v):(v,1)).reduceByKey(lambda a,b:a+b)#.items()
    #print flattedTweetHashtagsRDD.take(10)
    sortedHashtagCounts=sorted(hashtagCounts.collect(),key=lambda x:x[1],reverse=True)
    print sortedHashtagCounts
    topHashtagCounts=sortedHashtagCounts[:N] if N<len(sortedHashtagCounts) else sortedHashtagCounts

    [HashtagBenchmark(creationdate=creationdate,subscriber=request.session["username"],hashtag=t[0],count=t[1]).save() for t in topHashtagCounts]
    timeBasedTaggedRDD=flattedTweetHashtagsRDD.map(lambda ((tn,tObj),tag):(Row(created=tn.createdAt,tag=tag,tweetObj=tObj))).cache()
    if tMode=="yearly":
        groupedRDD=timeBasedTaggedRDD.groupBy(lambda record:(record.created.year,record.created.month,record.tag))
        timeBasedHashtagCounts=groupedRDD.mapValues(len)
        [HashtagTimeline(creationdate=creationdate,subscriber=request.session["username"],year=t[0][0],month=t[0][1],hashtag=t[0][2],count=t[1]).save() for t in timeBasedHashtagCounts.collect()]
        sentimentResultsRDD=timeBasedRDD.filter(lambda record: "Ford" in record.subscriber).map(lambda record:((record.created.year,record.created.month),(record.tweetObj.obj_Score,record.tweetObj.neg_Score,record.tweetObj.pos_Score,1))).filter(lambda (k,v):v[0]!=None).reduceByKey(lambda x,y:(x[0]+y[0],x[1]+y[1],x[2]+y[2],x[3]+y[3]))
        [SentimentTimeline(creationdate=creationdate,subscriber=request.session["username"],year=t[0][0],month=t[0][1],obj_score=t[1][0]/float(t[1][3]),neg_score=t[1][1]/float(t[1][3]),pos_score=t[1][2]/float(t[1][3])).save() for t in sentimentResultsRDD.collect()]
        subscriberPairedRDD=timeBasedRDD.map(lambda record:((record.created.year,record.created.month,record.subscriber[0]),(1,record.tnObj.retweets.count())))
        competitorCountsRDD=subscriberPairedRDD.reduceByKey(lambda a,b:(a[0]+b[0],a[1]+b[1]))
        [TweetCompetitionTimeline(creationdate=creationdate,year=t[0][0],month=t[0][1],subscriber=t[0][2],tweetcount=t[1][0],retweetcount=t[1][1]).save() for t in competitorCountsRDD.collect()]
    elif tMode=="monthly":
        groupedRDD=timeBasedTaggedRDD.groupBy(lambda record:(record.created.month,record.tag))
        timeBasedHashtagCounts=groupedRDD.mapValues(len)
        [HashtagTimeline(creationdate=creationdate,subscriber=request.session["username"],month=t[0][0],hashtag=t[0][1].encode('ascii','ignore'),count=t[1]).save() for t in timeBasedHashtagCounts.collect()]
        sentimentResultsRDD=timeBasedRDD.filter(lambda record: "Ford" in record.subscriber).map(lambda record:(record.created.month,(record.tweetObj.obj_Score,record.tweetObj.neg_Score,record.tweetObj.pos_Score,1))).filter(lambda (k,v):v[0]!=None).reduceByKey(lambda x,y:(x[0]+y[0],x[1]+y[1],x[2]+y[2],x[3]+y[3]))
        [SentimentTimeline(creationdate=creationdate,subscriber=request.session["username"],month=t[0],obj_score=t[1][0]/float(t[1][3]),neg_score=t[1][1]/float(t[1][3]),pos_score=t[1][2]/float(t[1][3])).save() for t in sentimentResultsRDD.collect()]
        subscriberPairedRDD=timeBasedRDD.map(lambda record:((record.created.month,record.subscriber[0]),(1,record.tnObj.retweets.count())))
        competitorCountsRDD=subscriberPairedRDD.reduceByKey(lambda a,b:(a[0]+b[0],a[1]+b[1]))
        [TweetCompetitionTimeline(creationdate=creationdate,month=t[0][0],subscriber=t[0][1],tweetcount=t[1][0],retweetcount=t[1][1]).save() for t in competitorCountsRDD.collect()]
    elif tMode=="weekly":
        groupedRDD=timeBasedTaggedRDD.groupBy(lambda record:(week_of_month(record.created),record.tag))
        timeBasedHashtagCounts=groupedRDD.mapValues(len)
        [HashtagTimeline(creationdate=creationdate,subscriber=request.session["username"],week=t[0][0],hashtag=t[0][1].encode('ascii','ignore'),count=t[1]).save() for t in timeBasedHashtagCounts.collect()]
        sentimentResultsRDD=timeBasedRDD.filter(lambda record: "Ford" in record.subscriber).map(lambda record:(week_of_month(record.created),(record.tweetObj.obj_Score,record.tweetObj.neg_Score,record.tweetObj.pos_Score,1))).filter(lambda (k,v):v[0]!=None).reduceByKey(lambda x,y:(x[0]+y[0],x[1]+y[1],x[2]+y[2],x[3]+y[3]))
        [SentimentTimeline(creationdate=creationdate,subscriber=request.session["username"],week=t[0],obj_score=t[1][0]/float(t[1][3]),neg_score=t[1][1]/float(t[1][3]),pos_score=t[1][2]/float(t[1][3])).save() for t in sentimentResultsRDD.collect()]
        subscriberPairedRDD=timeBasedRDD.map(lambda record:((week_of_month(record.created),record.subscriber[0]),(1,record.tnObj.retweets.count())))
        competitorCountsRDD=subscriberPairedRDD.reduceByKey(lambda a,b:(a[0]+b[0],a[1]+b[1]))
        [TweetCompetitionTimeline(creationdate=creationdate,week=t[0][0],subscriber=t[0][1],tweetcount=t[1][0],retweetcount=t[1][1]).save() for t in competitorCountsRDD.collect()]
    else:
        groupedRDD=timeBasedTaggedRDD.groupBy(lambda record:(record.created.day,record.tag))
        timeBasedHashtagCounts=groupedRDD.mapValues(len)
        [HashtagTimeline(creationdate=creationdate,subscriber=request.session["username"],day=t[0][1],hashtag=t[0][2].encode('ascii','ignore'),count=t[1]).save() for t in timeBasedHashtagCounts.collect()]
        sentimentResultsRDD=timeBasedRDD.filter(lambda record: "Ford" in record.subscriber).map(lambda record:(record.day,(record.tweetObj.obj_Score,record.tweetObj.neg_Score,record.tweetObj.pos_Score,1))).filter(lambda (k,v):v[0]!=None).reduceByKey(lambda x,y:(x[0]+y[0],x[1]+y[1],x[2]+y[2],x[3]+y[3]))
        [SentimentTimeline(creationdate=creationdate,subscriber=request.session["username"],day=t[0],obj_score=t[1][0]/float(t[1][3]),neg_score=t[1][1]/float(t[1][3]),pos_score=t[1][2]/float(t[1][3])).save() for t in sentimentResultsRDD.collect()]
        subscriberPairedRDD=timeBasedRDD.map(lambda record:((record.day,record.subscriber[0]),(1,record.tnObj.retweets.count())))
        competitorCountsRDD=subscriberPairedRDD.reduceByKey(lambda a,b:(a[0]+b[0],a[1]+b[1]))
        [TweetCompetitionTimeline(creationdate=creationdate,day=t[0][0],subscriber=t[0][1],tweetcount=t[1][0],retweetcount=t[1][1]).save() for t in competitorCountsRDD.collect()]


def calculateRanking(subscriber,sorted_count_list):
    rank=0
    for i,(k,v) in enumerate(sorted_count_list):
        if k==subscriber:
            rank=i+1
            break
    return rank


