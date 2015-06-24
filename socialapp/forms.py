__author__ = 'anil'
from django import forms
from datetimewidget.widgets import DateTimeWidget,DateWidget,TimeWidget
class testFormBootstrap3(forms.Form):
    dateTimeOptions = {'format': 'dd-mm-yyyy HH:ii P','autoclose': True,'showMeridian' : True,'minView':1,'startView':3,'todayHighlight': True,'clearBtn':False}
    dateTimeOptions = {'autoclose': True,'todayHighlight': True,'clearBtn':False}
    #date_time = forms.DateTimeField(widget=DateTimeWidget(usel10n=True, bootstrap_version=3,options = dateTimeOptions))
    start_date = forms.DateField(widget=DateWidget(usel10n=True, bootstrap_version=3,options = dateTimeOptions))
    end_date = forms.DateField(widget=DateWidget(usel10n=True, bootstrap_version=3,options = dateTimeOptions))
    #time = forms.TimeField(widget=TimeWidget(usel10n=True, bootstrap_version=3))
