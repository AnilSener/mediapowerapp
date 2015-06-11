#from django.db import models
from mongoengine import *
import math
from neo4django.db import models
#from neo4django.graph_auth.models import User, UserManager
# Create your models here.
import nltk
from nltk.corpus import sentiwordnet as swn
wnl = nltk.WordNetLemmatizer()

class Tweet(Document):
    geometry = PolygonField()
    geopoint = GeoPointField()
    timestamp = DateTimeField()
    placeId = StringField()
    placeFullName = StringField()
    placeName = StringField()
    countryCode = StringField()
    placeType = StringField()
    language = StringField()
    text = StringField()
    createdAt = DateTimeField()
    isRetweeted = BooleanField()
    isFavorited = BooleanField()
    retweetCount = LongField()
    favoriteCount = LongField()
    trends = ListField()
    hashtags = ListField()
    symbols = ListField()
    urls = ListField()
    twitteruser = ReferenceField("TwitterUser")
    pos_Score= LongField()
    obj_Score= LongField()
    neg_Score= LongField()
    def calculate_Sentiment_Scores(self):
        sentences = nltk.sent_tokenize(self.text)
        stokens = [nltk.word_tokenize(sent) for sent in sentences]
        taggedlist=[]
        for stoken in stokens:
            taggedlist.append(nltk.pos_tag(stoken))
        wordcnt=0
        for idx,taggedsent in enumerate(taggedlist):
            for idx2,t in enumerate(taggedsent):
                newtag=self.conv_pos(t[1])
                lemmatized=wnl.lemmatize(t[0])
                synsets = list(swn.senti_synsets(lemmatized, newtag))
                self.pos_Score+=synsets[0].pos_score()
                self.neg_Score=synsets[0].neg_score()
                self.obj_Score=synsets[0].obj_score()
                wordcnt+=1
        if wordcnt>1:
            self.pos_Score=self.pos_Score/wordcnt
            self.obj_Score=self.obj_Score/wordcnt
            self.neg_Score=self.neg_Score/wordcnt
        self.save()


    def conv_pos(x):
        if x[:2] == 'NN':
            return 'n';
        elif x[:2] == 'JJ':
            return 'a';
        elif x[:1] == 'V':
            return 'v';
        elif x[:1] == 'R':
            return 'r';
        else:
            return None;


class TweetNode(models.NodeModel):
    tweetID= models.IntegerProperty()
    in_reply_to_status_id=models.IntegerProperty()
    owner = models.Relationship('TwitterUser',rel_type='tweeted_by',related_name="tweets")
    objectID=models.StringProperty()
    replies = models.Relationship('self',rel_type='replied_as')


"""class TwitterUser(Document):
    userID = StringField()
    userName = StringField()
    retweetCount = LongField()
    friendsCount = LongField()
    followersCount = LongField()
    isGeoEnabled = BooleanField
    language = StringField()
    def gettweetObjIDs(self):
        return self.tweetObjIDs"""

class TwitterUser(models.NodeModel):
    userID = models.StringProperty()
    userName = models.StringProperty()
    retweetCount = models.IntegerProperty()
    friendsCount = models.IntegerProperty()
    followersCount = models.IntegerProperty()
    isGeoEnabled = models.BooleanProperty()
    language = models.StringProperty()
    #tweets = models.Relationship('TweetNode',rel_type='tweets')

from mongoengine.django.auth import User
qs=User.objects.all()
if len(qs[:])==0:
    user = User.create_user(username='default', email='default@default.com', password='defaultpassword')
"""class SubscriberTwitterUser(User):
    objects = UserManager()
    follows = models.Relationship('self', rel_type='follows',related_name='followed_by')"""

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


