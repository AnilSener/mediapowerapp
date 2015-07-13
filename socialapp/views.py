# Create your views here.


from socialapp.models import Subscriber


from django.template import RequestContext
from django.shortcuts import render_to_response

from django.contrib.auth import authenticate
from runipy.notebook_runner import NotebookRunner
from IPython.nbformat.current import read
from django_tables2 import RequestConfig
from pytz import timezone
from analytics.kpi_calculations import *
from analytics.charts import *
from socialapp.forms import testFormBootstrap3
from util import getTimelineMode
def main_view(request):
    response_dict={"response_msg":""};target='index.html'
    #generating a dummy userID for session since each user will have to work concurrently their inputs should be independent from each other

    user=authenticate(username='Ford', password='defaultpassword')
    if user.is_authenticated():
        s=Subscriber.objects.filter(name=user.username).get()
        if s!=None:
            request.session["username"]=user.username
            form = None
            if request.GET.get('id',None):
                form = testFormBootstrap3(instance=testFormBootstrap3.objects.get(id=request.GET.get('id',None)))
            else:
                form = testFormBootstrap3()
            response_dict['form']=form
            if request.method == 'GET' and request.session!=None:
                today=datetime.datetime.today().replace(tzinfo=timezone('UTC'))
                startDate=today.replace(year=today.year-1) if not 'start_date' in request.GET else datetime.datetime.strptime(request.GET['start_date'],"%Y-%m-%d").replace(tzinfo=timezone('UTC'))
                endDate=today if not 'end_date' in request.GET else datetime.datetime.strptime(request.GET['end_date'],"%Y-%m-%d").replace(tzinfo=timezone('UTC'))
                print startDate
                print endDate
                print "user",request.session["username"]
                tMode=getTimelineMode(startDate,endDate)
                #calculateKPIs(request,tMode,startDate,endDate)
                response_dict["startDate"]=startDate.strftime("%d-%m-%Y")
                response_dict["endDate"]=endDate.strftime("%d-%m-%Y")
                response_dict["subscriber"]=request.session["username"]
                response_dict["charts"]=[]
                response_dict["charts"].append(getTopHashtagChart(request.session["username"]))
                response_dict["charts"].append(getHashTagTimeline(request.session["username"],tMode))
                response_dict["charts"].append(getSentimentTimeline(request.session["username"],tMode))
                response_dict["charts"].append(getTweetCompetitionTimeline(request.session["username"],tMode))
                response_dict["charts"].append(getCountryFollowerPieChart(request.session["username"]))
                qs=CompetitorBenchmark.objects.filter(subscriber=request.session["username"])
                benchmarkObj=qs.filter(creationdate=qs.latest('creationdate').creationdate).all()
                table = CompetitorBenchmarkingResultsTable(benchmarkObj)
                RequestConfig(request).configure(table)
                response_dict["table"]=table
                response_dict["response_msg"]+="Welcome to Mediapower Social Scoring Application!"
                return render_to_response(target,response_dict,context_instance=RequestContext(request))
            else:
                response_dict["response_msg"]+="Welcome to Mediapower Social Scoring Application!"
                return render_to_response(target,response_dict,context_instance=RequestContext(request))
    else:
        response_dict["response_msg"]+="Welcome to Mediapower Social Scoring Application!"
        return render_to_response(target,response_dict,context_instance=RequestContext(request))

def map(request):
    target='map.html'
    return render_to_response(target,{},context_instance=RequestContext(request))

from django.http import HttpResponse
import json
def getFollowers(request):
    qs=GeoFollower.objects.filter(subscriber="Ford")



    features=[]
    for record in qs.filter(creationdate=qs.latest('creationdate').creationdate).all():
        feature={"type":"Feature","geometry":{"type":"Point","coordinates":[record.geopointX,record.geopointY]},"properties":{"followerCount":record.count,"placeName":record.placeName}}
        features.append(feature)

    my_layer = {
    "type": "FeatureCollection",
    "features": features,
    "crs": {
        "type": "link",
        "properties": {"href": "http://spatialreference.org/ref/epsg/4326", "type": "proj4"}}}
    followerjson=json.dumps(my_layer, ensure_ascii=False)
    print followerjson
    return HttpResponse(followerjson, content_type="application/json")

def getGraphEdges(request):
    features=[]
    for s in Subscriber.objects.all():
        print "Graph Subscriber",s.name
        for user in s.twitterusers.all():
            features.append({"subscriber":s.name,"user":user.userName,"followerCount":user.followersCount})

    graphjson=json.dumps(features, ensure_ascii=False)
    print graphjson
    return HttpResponse(graphjson, content_type="application/json")
