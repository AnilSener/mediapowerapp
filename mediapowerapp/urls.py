from django.conf.urls import patterns, include, url
from socialapp import views
from tastypie.api import Api
from socialapp.api import *
v1_api = Api(api_name='v1')
v1_api.register(SubscriberResource())
# Uncomment the next two lines to enable the admin:
"""from django.contrib import admin
admin.autodiscover()"""
from neo4django import admin

admin.autodiscover()
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mediapowerapp.views.home', name='home'),
    # url(r'^mediapowerapp/', include('mediapowerapp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^socialapp/$',views.main_view,name='main_view'),
    url(r'^api/', include(v1_api.urls)),
    url(r'^socialapp/get-followers/$', views.getFollowers, name='get_followers'),
    url(r'^socialapp/map/$',views.map,name='map'),
    url(r'^socialapp/get-graphedges/$',views.getGraphEdges, name='get_graphedges'),
)
