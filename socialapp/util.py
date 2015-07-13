__author__ = 'anil'
import datetime
import calendar
def week_of_month(tgtdate):

    days_this_month = calendar.mdays[tgtdate.month]
    for i in range(1, days_this_month):
        d = datetime.date(tgtdate.year, tgtdate.month, i)
        if d.day - d.weekday() > 0:
            startdate = d
            break
    # now we canuse the modulo 7 appraoch
    return (tgtdate - startdate).days //7 + 1

def getTimelineMode(startDate,endDate):
    if (endDate.year-startDate.year)>1 or ((endDate.year-startDate.year)==1 and endDate.month>=endDate.month):
        return "yearly"
    elif endDate.year==startDate.year and (endDate.month-endDate.month)>1:
        return "monthly"
    elif endDate.year==startDate.year and (endDate.month-endDate.month)==1:
        return "weekly"
    else:
        return "daily"