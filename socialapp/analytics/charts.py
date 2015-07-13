__author__ = 'anil'
from chartit import DataPool, Chart,PivotChart,PivotDataPool
from socialapp.models import *

def getTopHashtagChart(subscriber):
    qs=HashtagBenchmark.objects.filter(subscriber=subscriber)
    ds = DataPool(
       series=
        [{'options': {
            'source': qs.filter(creationdate=qs.latest('creationdate').creationdate).all()},
          'terms': [
            'hashtag',
            'count']}
         ])

    cht = Chart(
        datasource = ds,
        series_options =
          [{'options':{
              'type': 'column',
              'stacking': True},
            'terms':{
              'hashtag': [
                'count']
              }}],
        chart_options =
          {'title': {
               'text': 'Top Hashtags by No of Tweets'},
           'xAxis': {
                'title': {
                   'text': 'Hashtag Name'}},
           'yAxis': {
                'title': {
                   'text': 'Tweet Count'}}
           })
    return cht

from django.db.models import Sum
def getHashTagTimeline(subscriber,tMode):
    categories=[]
    xText=""
    if tMode=="yearly":
        categories=['year','month']
        xText="Year:Month"
    elif tMode=="monthly":
        categories=['month']
        xText="Month"
    elif tMode=="weekly":
        categories=['month','week']
        xText="Week"
    else:
        categories=['day']
        xText="Day"
    qs=HashtagTimeline.objects.filter(subscriber=subscriber)
    pivotdata = PivotDataPool(
           series =
            [{'options': {
               'source': qs.filter(creationdate=qs.latest('creationdate').creationdate).all(),
               'categories': categories,
                'legend_by': ['hashtag']},
              'terms': {
                'count': Sum('count')}
              }
             ])


    #Step 2: Create the PivotChart object
    pivcht = PivotChart(
            datasource = pivotdata,
            series_options =
              [{'options':{
                  'type': 'line',
                  'stacking': False},
                'terms':[
                  'count']}],
            chart_options =
              {'title': {
                   'text': 'Hashtag Tweet Counts per '+xText},
               'xAxis': {
                    'title': {
                       'text': xText}},
               'yAxis': {
                'title': {
                   'text': 'Tweet Count'}}
               })
    return pivcht


def getSentimentTimeline(subscriber,tMode):
    categories=[]
    xText=""
    if tMode=="yearly":
        categories=['year','month']
        xText="Year:Month"
    elif tMode=="monthly":
        categories=['month']
        xText="Month"
    elif tMode=="weekly":
        categories=['month','week']
        xText="Week"
    else:
        categories=['day']
        xText="Day"
    qs=SentimentTimeline.objects.filter(subscriber=subscriber)
    pivotdata = PivotDataPool(
           series =
            [{'options': {
               'source': qs.filter(creationdate=qs.latest('creationdate').creationdate).all(),
               'categories': categories},
              'terms': {
                  'Objective_Score':Sum('obj_score'),
                'Negative_Score':Sum('neg_score'),
                'Positive_Score':Sum('pos_score')}
              }
             ])


    #Step 2: Create the PivotChart object
    pivcht = PivotChart(
            datasource = pivotdata,
            series_options =
              [{'options':{
                  'type': 'line',
                  'stacking': False},
                'terms':[
                  'Objective_Score',
                'Negative_Score',
                'Positive_Score']}],
            chart_options =
              {'title': {
                   'text': 'Average Sentiment Score per '+xText},
               'xAxis': {
                    'title': {
                       'text': xText}},
               'yAxis': {
                'title': {
                   'text': 'Average Sentiment Score'}}
               })

    return pivcht

def getTweetCompetitionTimeline(subscriber,tMode):
    categories=[]
    xText=""
    if tMode=="yearly":
        categories=['year','month']
        xText="Year:Month"
    elif tMode=="monthly":
        categories=['month']
        xText="Month"
    elif tMode=="weekly":
        categories=['month','week']
        xText="Week"
    else:
        categories=['day']
        xText="Day"
    qs=TweetCompetitionTimeline.objects.all()
    pivotdata = PivotDataPool(
           series =
            [{'options': {
               'source': qs.filter(creationdate=qs.latest('creationdate').creationdate).all(),
               'categories': categories,
                'legend_by': ['subscriber']},
              'terms': {
                'Tweet Count': Sum('tweetcount')}
              }
             ])


    #Step 2: Create the PivotChart object
    pivcht = PivotChart(
            datasource = pivotdata,
            series_options =
              [{'options':{
                  'type': 'line',
                  'stacking': False},
                'terms':[
                  'Tweet Count']}],
            chart_options =
              {'title': {
                   'text': 'Tweet Counts compared to Competitors per '+xText},
               'xAxis': {
                    'title': {
                       'text': xText}},
               'yAxis': {
                'title': {
                   'text': 'Tweet Count'}}
               })
    return pivcht

def getCountryFollowerPieChart(subscriber):
    qs=CountryFollower.objects.filter(subscriber=subscriber)
    ds = DataPool(
       series=
        [{'options': {
            'source': qs.filter(creationdate=qs.latest('creationdate').creationdate).all()},
          'terms': [
            'code',
            'count']}
         ])
    def countryname(code):
        return Country.objects.filter(code=code).get().name


    cht = Chart(
        datasource = ds,
        series_options =
          [{'options':{
              'type': 'pie',
              'stacking': False},
            'terms':{
              'code': [
                'count']
              }}],
        chart_options =
          {'title': {
               'text': 'Followers By Country'},
           'xAxis': {
                'title': {
                   'text': 'Country'}}
           },
        x_sortf_mapf_mts = (None, countryname, False))
    return cht