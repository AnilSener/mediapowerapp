__author__ = 'anil'
from chartit import DataPool, Chart
from socialapp.models import *

def getTopHashtagChart(subscriber):

    ds = DataPool(
       series=
        [{'options': {
            'source': HashtagBenchmark.objects.filter(subscriber=subscriber).all()[:5]},
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
                   'text': 'Hashtag Name'}}})
    return cht