__author__ = 'anil'

from socialapp.models import Subscriber
s=Subscriber.objects(name="Ford").get()