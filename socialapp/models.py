#from django.db import models
from mongoengine import *
import math
from neo4django.db import models
from django.db import models as dbmodels
#from neo4django.graph_auth.models import User, UserManager
# Create your models here.
import nltk
from nltk.corpus import sentiwordnet as swn
wnl = nltk.WordNetLemmatizer()
import numpy as np
import math

class Place(Document):
    geometry = PolygonField()
    geopoint = GeoPointField()
    placeId = StringField()
    placeFullName = StringField()
    placeName = StringField()
    country = StringField()
    countryCode = StringField()
    placeType = StringField()
    tweetID = StringField()
    location = StringField()

class PlaceNode(models.NodeModel):
    placeId = models.StringProperty(primary_key=True)
    placeFullName = models.StringProperty()
    placeName = models.StringProperty()
    country = models.StringProperty()
    countryCode = models.StringProperty()
    placeType = models.StringProperty()
    resident = models.Relationship('TwitterUser',rel_type='resides_in',related_name="locations")
    tweetLocation = models.Relationship('TweetNode',rel_type='tweeted_in',related_name="places")
    location= models.StringProperty()
class Tweet(Document):
    tweetID= StringField(primary_key=True)
    #location= EmbeddedDocumentField('Place')
    language = StringField()
    text = StringField()
    cleaned_text = StringField()
    createdAt = DateTimeField()
    isRetweeted = BooleanField()
    isFavorited = BooleanField()
    retweetCount = LongField()
    favoriteCount = LongField()
    trends = ListField()
    #hashtags = ListField()
    symbols = ListField()
    urls = ListField()
    twitteruser = ReferenceField("TwitterUser")
    pos_Score= FloatField()
    obj_Score= FloatField()
    neg_Score= FloatField()
    def calculate_Sentiment_Scores(self):
        sentences = nltk.sent_tokenize(self.cleaned_text)
        stokens = [nltk.word_tokenize(sent) for sent in sentences]
        taggedlist=[]
        for stoken in stokens:
            taggedlist.append(nltk.pos_tag(stoken))
        print taggedlist
        pos_scores=[];obj_scores=[];neg_scores=[]
        for idx,taggedsent in enumerate(taggedlist):
            print idx,taggedsent
            for idx2,t in enumerate(taggedsent):
                print t
                newtag=conv_pos(t[1])
                lemmatized=wnl.lemmatize(t[0])
                print(newtag)
                print(lemmatized)
                synsets = list(swn.senti_synsets(lemmatized.lower(), newtag))
                if len(synsets)>0:
                    pos_scores.append(synsets[0].pos_score())
                    neg_scores.append(synsets[0].neg_score())
                    obj_scores.append(synsets[0].obj_score())
        pos_scores=[x for x in pos_scores if not math.isnan(x)]
        obj_scores=[x for x in obj_scores if not math.isnan(x)]
        neg_scores=[x for x in neg_scores if not math.isnan(x)]
        self.pos_Score=np.mean(pos_scores) if len(pos_scores)>0 else 0
        self.obj_Score=np.mean(obj_scores) if len(obj_scores)>0 else 0
        self.neg_Score=np.mean(neg_scores) if len(neg_scores)>0 else 0
        print self.pos_Score
        self.save()


def conv_pos(x):
    if x[:2] == 'NN' and not x == 'NNP':
        return 'n';
    elif x[:2] == 'JJ':
        return 'a';
    elif x[:1] == 'V':
        return 'v';
    elif x[:1] == 'R':
        return 'r';
    elif x[:2] == 'RB':
        return 'adv'
    else:
        return None;


class TweetNode(models.NodeModel):
    tweetID= models.StringProperty()
    in_reply_to_status_id=models.StringProperty()
    owner = models.Relationship('TwitterUser',rel_type='tweeted_by',related_name="tweets")
    createdAt = models.DateTimeProperty()
    repliedto = models.Relationship('self',rel_type='replied_as',related_name="replies")
    retweeted = models.Relationship('self',rel_type='retweeted_as',related_name="retweets")


class HashTag(models.NodeModel):
    tag = models.StringProperty()
    tweets = models.Relationship('TweetNode',rel_type='tagged_in',related_name="hashtags")
    users = models.Relationship('TwitterUser',rel_type='tagged_for',related_name="hashtags")

class Emoticon(models.NodeModel):
    type = models.StringProperty()
    tweets = models.Relationship('TweetNode',rel_type='expresses',related_name="emoticons")
    users = models.Relationship('TwitterUser',rel_type='feels',related_name="emoticons")

class TwitterRegistry(dbmodels.Model):
    id=dbmodels.AutoField(primary_key=True)
    subscriberName=dbmodels.TextField()
    twitterUserName=dbmodels.TextField()

#Chart Models
class HashtagBenchmark(dbmodels.Model):
    id=dbmodels.AutoField(primary_key=True)
    creationdate=dbmodels.DateTimeField()
    subscriber=dbmodels.TextField()
    hashtag = dbmodels.TextField()
    count = dbmodels.IntegerField()
    class Meta:
        ordering=('subscriber','-creationdate','-count')

class CountryFollower(dbmodels.Model):
    id=dbmodels.AutoField(primary_key=True)
    creationdate=dbmodels.DateTimeField()
    subscriber=dbmodels.TextField()
    code = dbmodels.TextField()
    count = dbmodels.IntegerField()
    class Meta:
        ordering=('subscriber','-creationdate')

class GeoFollower(dbmodels.Model):
    id=dbmodels.AutoField(primary_key=True)
    creationdate=dbmodels.DateTimeField()
    placeName=dbmodels.TextField()
    subscriber=dbmodels.TextField()
    geopointX = dbmodels.DecimalField(decimal_places=8,max_digits=30)
    geopointY = dbmodels.DecimalField(decimal_places=8,max_digits=30)
    count = dbmodels.IntegerField()
    class Meta:
        ordering=('subscriber','-creationdate')

#Chart Models
class HashtagTimeline(dbmodels.Model):
    id=dbmodels.AutoField(primary_key=True)
    creationdate=dbmodels.DateTimeField()
    subscriber=dbmodels.TextField()
    hashtag = dbmodels.TextField()
    year = dbmodels.IntegerField()
    month = dbmodels.IntegerField()
    week = dbmodels.IntegerField()
    day = dbmodels.IntegerField()
    count = dbmodels.IntegerField()
    class Meta:
        ordering=('subscriber','-creationdate','year','month','week','day')

class SentimentTimeline(dbmodels.Model):
    id=dbmodels.AutoField(primary_key=True)
    creationdate=dbmodels.DateTimeField()
    subscriber=dbmodels.TextField()
    year = dbmodels.IntegerField()
    month = dbmodels.IntegerField()
    week = dbmodels.IntegerField()
    day = dbmodels.IntegerField()
    obj_score = dbmodels.FloatField()
    neg_score = dbmodels.FloatField()
    pos_score = dbmodels.FloatField()
    class Meta:
        ordering=('subscriber','-creationdate','year','month','week','day')

class TweetCompetitionTimeline(dbmodels.Model):
    id=dbmodels.AutoField(primary_key=True)
    creationdate=dbmodels.DateTimeField()
    subscriber=dbmodels.TextField()
    year = dbmodels.IntegerField()
    month = dbmodels.IntegerField()
    week = dbmodels.IntegerField()
    day = dbmodels.IntegerField()
    tweetcount = dbmodels.IntegerField()
    retweetcount = dbmodels.IntegerField()
    class Meta:
        ordering=('-creationdate','year','month','week','day')

class Country(dbmodels.Model):
    code=dbmodels.TextField(primary_key=True)
    name=dbmodels.TextField()

class Subscriber(models.NodeModel):
    name=models.StringProperty()#indexed=True, unique=True should be added


class TwitterUser(models.NodeModel):
    userID = models.StringProperty()
    userName = models.StringProperty()
    retweetCount = models.IntegerProperty()
    friendsCount = models.IntegerProperty()
    favouriteCount = models.IntegerProperty()
    followersCount = models.IntegerProperty()
    isGeoEnabled = models.BooleanProperty()
    language = models.StringProperty()
    account = models.Relationship('Subscriber',rel_type='owns',related_name="twitterusers")
    follower = models.Relationship('self', rel_type='follows',related_name='followers')

    #tweets = models.Relationship('TweetNode',rel_type='tweets')
s=Subscriber.objects.all()
if len(s[:])==0:
    Subscriber.objects.create(name="Ford")
    Subscriber.objects.create(name="Chevrolet")
    for s in Subscriber.objects.all():
        registry=TwitterRegistry.objects.filter(subscriberName=s.name).all()
        twitterAccounts=registry.values_list('twitterUserName',flat=True)
        for name in twitterAccounts:
            print name
            tu=TwitterUser.objects.create(userName=name)
            s.twitterusers.add(tu)
        s.save()



from mongoengine.django.auth import User
qs=User.objects.all()
if len(qs[:])==0:
    user = User.create_user(username='Ford', email='default@default.com', password='defaultpassword')
    user.set_password('defaultpassword')
"""class SubscriberTwitterUser(User):
    objects = UserManager()
    follows = models.Relationship('self', rel_type='follows',related_name='followed_by')"""

class CompetitorBenchmark(dbmodels.Model):
    id=dbmodels.AutoField(primary_key=True)
    KPI = dbmodels.TextField()
    subscriber=dbmodels.TextField()
    subscribervalue = dbmodels.DecimalField(decimal_places=4,max_digits=30,verbose_name="Subscriber's Value")
    average = dbmodels.DecimalField(decimal_places=4,max_digits=30,verbose_name='Industrial Average')
    ranking = dbmodels.IntegerField(verbose_name='Ranking')
    creationdate=dbmodels.DateTimeField()
    class Meta:
        ordering=('subscriber','-creationdate')

import django_tables2 as tables
class CompetitorBenchmarkingResultsTable(tables.Table):

    class Meta:
        model = CompetitorBenchmark
        # add class="paleblue" to <table> tag
        attrs = {"class": "paleblue","height":'70%'}
        exclude= ("id","subscriber","creationdate")



class BoundingBox(object):
    def __init__(self, *args, **kwargs):
        self.lat_min = None
        self.lon_min = None
        self.lat_max = None
        self.lon_max = None

    def get_Max_Radius(self):

        assert self.lat_min >= -90.0 and self.lat_min  <= 90.0 and self.lat_max >= -90.0 and self.lat_max  <= 90.0
        assert self.lon_min >= -180.0 and self.lon_min  <= 180.0 and self.lon_max >= -180.0 and self.lon_max  <= 180.0

        R = 6373.0

        lat1 = math.radians(self.lat_min)
        lon1 = math.radians(self.lon_min)
        lat2 = math.radians(self.lat_max)
        lon2 = math.radians(self.lon_max)

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = (math.sin(dlat/2))**2 + math.cos(lat1) * math.cos(lat2) * (math.sin(dlon/2))**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        radius=distance/2
        return radius
    def get_Center(self):
        return [(self.lon_min+self.lon_max)/2,(self.lat_min+self.lat_max)/2]


