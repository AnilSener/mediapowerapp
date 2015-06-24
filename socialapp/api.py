__author__ = 'anil'
from socialapp.models import *
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
class SubscriberResource (ModelResource): #it doesn't work with Resource neither
    class Meta:
        queryset= Subscriber.objects.all()
        resource_name = 'subscriber'
        authorization= Authorization()
        allowed_methods = ['get']
    def __unicode__(self):
        return self

class TweetNodeResource (ModelResource): #it doesn't work with Resource neither
    class Meta:
        queryset= TweetNode.objects.all()
        resource_name = 'tweetnode'
        authorization= Authorization()
    def __unicode__(self):
        return self