# Create your views here.


from socialapp.models import Subscriber


from django.template import RequestContext
from django.shortcuts import render_to_response
from datetime import datetime
from django.contrib.auth import authenticate
from runipy.notebook_runner import NotebookRunner
from IPython.nbformat.current import read
from django_tables2 import RequestConfig
def main_view(request):
    response_dict={"response_msg":""};target='index.html'
    #generating a dummy userID for session since each user will have to work concurrently their inputs should be independent from each other
    authenticate(username='default', password='defaultpassword')
    if request.user.is_authenticated():
        s=Subscriber.objects(name="Ford").get()
        if len(s[:])==0:
            request.session["userID"]=int(request.user.username)
            request.session["subscriber"]=s
            form = None
            response_dict['form']=form
            if request.session["s"]!=None:
                if request.method == 'GET' and len(request.GET)>0:
                    notebook = read(open("analytics/twitter_sna.ipynb"), 'json')
                    r = NotebookRunner(notebook, pylab=True)
                    r.run_notebook()
                    response_dict["response_msg"]+="Welcome to Mediapower Social Scoring Application!"
                    return render_to_response(target,response_dict,context_instance=RequestContext(request))
                else:
                    response_dict["response_msg"]+="Welcome to Mediapower Social Scoring Application!"
                    return render_to_response(target,response_dict,context_instance=RequestContext(request))
    else:
        response_dict["response_msg"]+="Welcome to Mediapower Social Scoring Application!"
        return render_to_response(target,response_dict,context_instance=RequestContext(request))

"""def main_view(request):
    response_dict={"response_msg":""};target='index.html'
    #generating a dummy userID for session since each user will have to work concurrently their inputs should be independent from each other
    if request.user.is_authenticated():
        s=Subscriber.objects(name="Ford").get()
        if len(s[:])==0:
            s=Subscriber.objects.create(name="Ford")
            s.save()
        authenticate(username='204269',password='johnpassword')
        request.session["userID"]=int(request.user.username)
    form = None
    response_dict['form']=form
    if request.session["userID"]!=None:
        me=MacroEcon.objects.filter(userID=request.session["userID"],isForecast=True).all()
        if me!=None:
            me=me.extra(order_by = ['-id'])
            table = HashTagResultsTable(me)
            response_dict["table"]=table
            RequestConfig(request).configure(table)
            if request.method == 'POST':
                form = UploadFileForm(request.POST, request.FILES)
                if form.is_valid():
                    result=storeUploadedFile(request.FILES['file'],request.session["userID"],datetime.strptime(request.POST["startdate"],"%m/%d/%Y"))
                    if result:
                        me=MacroEcon.objects.filter(userID=request.session["userID"],isForecast=True).all().extra(order_by = ['-id'])
                        table = HashTagResultsTable(me)
                        RequestConfig(request).configure(table)
                        response_dict["table"]=table
                        response_dict["response_msg"]+="All macro economical inputs are added to DB. You can now Forecast or Simulate the balance estimations."
                    else:
                        response_dict["response_msg"]+="Macro economical inputs cannot be added to DB."
                    return render_to_response(target,response_dict,context_instance=RequestContext(request))
                else:
                    response_dict["response_msg"]+="Please provide a date and a .tsv file and press 'Add' button to give new macro economical input.Then press 'Forecast' button to forecast the portfolio balance. "
                    return render_to_response(target,response_dict,context_instance=RequestContext(request))
            if request.method == 'GET' and len(request.GET)>0:
                if "Forecast" in request.GET or "Simulate" in request.GET:
                    me=MacroEcon.objects.filter(userID=request.session["userID"]).all()
                    if len(me[:])>0:
                        f=Forecast(me,request,"Forecast") if "Forecast" in request.GET else Forecast(me,request,"Simulate") if "Simulate" in request.GET else None
                        if f.status:
                            me=MacroEcon.objects.filter(userID=request.session["userID"],isForecast=True).all().extra(order_by = ['-id'])
                            table = HashTagResultsTable(me)
                            RequestConfig(request).configure(table)
                            response_dict["table"]=table
                            response_dict["response_msg"]+="Forecast Completed." if "Forecast" in request.GET else "Simulation Completed."
                        else:
                            response_dict["response_msg"]+="Please provide a date and a .tsv file and press 'Add' button to give new macro economical input.Then press 'Forecast' button to forecast the portfolio balance. "
                        return render_to_response(target,response_dict,context_instance=RequestContext(request))
                    else:
                        response_dict["response_msg"]+="Please provide a date and a .tsv file and press 'Add' button to give new macro economical input.Then press 'Forecast' button to forecast the portfolio balance. "
                        return render_to_response(target,response_dict,context_instance=RequestContext(request))
                else:
                    response_dict["response_msg"]+="Please provide a date and a .tsv file and press 'Add' button to give new macro economical input.Then press 'Forecast' button to forecast the portfolio balance. "
                    return render_to_response(target,response_dict,context_instance=RequestContext(request))
            else:
                response_dict["response_msg"]+="Please provide a date and a .tsv file and press 'Add' button to give new macro economical input.Then press 'Forecast' button to forecast the portfolio balance. "
                return render_to_response(target,response_dict,context_instance=RequestContext(request))
"""