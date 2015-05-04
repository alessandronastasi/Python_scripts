#!/usr/bin/python
# ******************************************************************************
#    Copyright 2015 IAS - IDOC
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ******************************************************************************
'''
This script plots the date/time statistics extracted from a log file.

@author: Alessandro NASTASI for IAS - IDOC 
@date: 04/05/2015
'''
__author__ = "Alessandro Nastasi"
__credits__ = ["Alessandro Nastasi"]
__license__ = "GPL"
__version__ = "1.0"
__date__ = "04/05/2015"

import sys,os, re
import matplotlib.pyplot as plt
import matplotlib.dates
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange
import datetime
import math
import numpy as np
import operator

import asciidata

from dateutil import parser

import urllib, json
from collections import Counter 
from numpy import arange


def hist_date(date_vector, lim_inf, lim_sup, dt = 1): # Default = 1day bin
  '''
  Create the bin of a datetime vector.
  Input:
  @date_vector : array of dates in DATETIME format (length = N)
  @lim_inf : min of the hist x-range, in DATETIME format (e.g., min(date_vector))
  @lim_sup : max of the hist x-range, in DATETIME format (e.g., max(date_vector))
  @dt : sampling interval (default = 1 day)
  
  Output:
  @bins4hist : array of date values (in float) for the histogram, with the latest values being lim_sup + 1 dt (length = N+1)
  @bins4plot : array of date values (in float) for the bar plot (length = N)
  @cnts : counts in each bins4hist (length = N)
  '''
  
  delta = datetime.timedelta(days = dt) # Bins of 24hrs

  #Convert the limits in order to start from 00:00:00 of the first day and finish on 23:59:59 of the last day
  lim_inf = float(int( matplotlib.dates.date2num(lim_inf) )) 
  lim_sup = math.ceil( matplotlib.dates.date2num(lim_sup) )
  
  #Convert datetime dates into floats
  date_vector_num = map(lambda x: matplotlib.dates.date2num(x), date_vector) # == date_num = matplotlib.dates.date2num(date_good)

  #Ned to re-convert into datetime format for the drange()
  lim_inf = matplotlib.dates.num2date(lim_inf)
  lim_sup = matplotlib.dates.num2date(lim_sup)

  #Create the array bins4plot with equally spaced dates, with step = dt
  #bins4plots contains N points, from lim_inf -> lim_sup
  bins4plot = drange(lim_inf, lim_sup, delta)

  #bins4hist contains N+1 points, from lim_inf -> lim_sup + 1 dt
  bins4hist = drange(lim_inf, lim_sup + datetime.timedelta(days = dt), delta)

  #Counts in each bins4hist
  cnts = np.histogram(date_vector_num, bins = bins4hist)[0]

  
  #date_vector_num = [matplotlib.dates.date2num(item) for item in date_vector] # Convert type(datetime) -> number
  #cnts = np.histogram(date_vector_num, bins = dt_limits)[0] # Counts for each dt, with width = delta

  #bins4hist = [0.5*(dt_limits[i] + dt_limits[i+1]) for i in range(len(dt_limits)-1)] # Re-compute the center of each bin in order to have same size counts and dt_i

  return bins4hist, bins4plot, cnts


def hist_weekday_hours(date_vector, time_shift = 0, plot_name = 'plot.png'): # Default time_shift = 0: local time = observed time (unless times already corrected)
  '''
  Create two histograms of a datetime vector, in bins of weekdays (0: Monday, 6: Sunday) and hours (0 - 23).
  Input:
  @date_vector : array of dates in DATETIME format (length = N)
  @time_shift : difference (in hours) between the local timezone and the recorded time
  @plot_name : name of the figure with two plots to produce.
  
  Output:
  @plot : figure with two plots
  '''
  
  fig = plt.figure(); plt_weekday = fig.add_subplot(211); plt_hours = fig.add_subplot(212)
  fig_title = 'Statistics of visits to SZ-DB from %s' % ( (plot_name.split('.')[0]).upper() )
  fig.suptitle(fig_title)
  # Time shift correction
  date_local = [ item + datetime.timedelta(hours = time_shift) for item in date_vector ]

  #Weekday
  weekdays = [x.weekday() for x in date_local]
  x_weekday = np.arange(0,8,1)
  cnts_weekdays = np.histogram(weekdays, bins=x_weekday)[0]
  plt_weekday.plot(x_weekday[:-1], cnts_weekdays, 'k-', alpha = 1)

  line_style = 'bo-' 
  for days in range(0,7):
    if days in [5, 6]: line_style = 'ro-'
    #plt_weekday.plot(x_weekday[:-1], cnts_weekdays, line_style, alpha = 0.9 - (days*0.1) )
    plt_weekday.plot(x_weekday[days], cnts_weekdays[days], line_style, alpha = 0.5)
  
  plt_weekday.grid()
  weekday_label = 'LOCAL weekday of visit' #'RECORDED weekday of visit'
  if time_shift != 0: weekday_label = 'LOCAL weekday of visit'
  plt_weekday.set_xlabel(weekday_label)
  plt_weekday.set_ylabel('# visits')
  plt_weekday.set_xlim(-0.5, 6.5)
  #x_labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  #plt_hours.xaxis.set_ticks(np.arange(0, 7, 1))
  plt_weekday.set_xticks(np.arange(0, 7, 1))
  plt_weekday.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
  fig.subplots_adjust(hspace=0.3)
  
  #Hours
  hours = [x.hour for x in date_local]
  x_hour = np.arange(0,25,1)
  cnts_hours = np.histogram(hours, bins=x_hour)[0]
  plt_hours.plot(x_hour[:-1], cnts_hours/(1.0*sum(cnts_weekdays)), 'k-',linewidth=2, alpha = 1 ) # *0.3
  
  #plt_hours.grid()
  #hour_label = 'RECORDED hour of visit'
  #if time_shift != 0: hour_label = 'LOCAL hour of visit'
  #plt_hours.set_xlabel(hour_label)
  #plt_hours.xaxis.set_ticks(np.arange(0, 24, 2))
  #plt_hours.set_xlim(0,23)
  #plt.savefig(plot_name, bbox_inches='tight')
  #print '\n> Figure saved in %s' % plot_name
  
  #Hours & weekdays
  x_hour = np.arange(0,25,1)
  line_style = 'b-'
  for days in range(0,7):
    hours = [x.hour for x in date_local if x.weekday() == days]
    cnts = np.histogram(hours, bins=x_hour)[0]
    if days in [5, 6]: line_style = 'r-'
    plt_hours.plot(x_hour[:-1], cnts/(1.0*cnts_weekdays[days]), line_style, alpha = 0.5)
    
  plt_hours.grid()
  hour_label = 'LOCAL daytime of visit'
  if time_shift != 0: hour_label = 'LOCAL daytime of visit'
  plt_hours.set_xlabel(hour_label)
  plt_hours.set_ylabel('# visits normalized per weekday counts')
  plt_hours.xaxis.set_ticks(np.arange(0, 24, 2))
  plt_hours.set_xlim(0,23)
  plt.savefig(plot_name, bbox_inches='tight')
  print '\n> Figure saved in %s' % plot_name

  return True

def get_gmtOffset(dict_obsDate):
  '''import sys,os, re

import matplotlib.pyplot as plt
import matplotlib.dates
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange
import datetime
import math
import numpy as np
import operator

import asciidata

from dateutil import parser

import urllib, json
from collections import Counter 
from numpy import arange

  Compute the time offset (in hours) from the GMT = +1 (Orsay Ville), given the lat and long of an IP
  
  Input:
  @dict_obsDate : contains IP, lat, lng, observed visit date (in datetime format)
  
  Output:
  @dict_localDate : contains IP, lat, lng, observed visit date (in datetime format), LOCAL visit date (in datetime format), gmtOffset (hours)
  '''
  for ip in dict_obsDate:
    lat = dict_obsDate[ip]['lat'][0]
    lon = dict_obsDate[ip]['lon'][0]
    
    url = "http://api.geonames.org/timezoneJSON?lat=%s&lng=%s&username=idoc_ias" % (lat, lon)
    response = urllib.urlopen(url)
    json_output = response.read()
    print ip, json_output
    data = json.loads(json_output)
    
    gmtOffset = data['gmtOffset']

    dict_obsDate[ip]['gmtOffset'] = gmtOffset
    
    #loop on the visit dates
    for i, dates in enumerate(dict_obsDate[ip]['visit_date']):
      loc_visitDate = dates + datetime.timedelta(hours = int(gmtOffset - 1) )
      if i == 0: dict_obsDate[ip]['local_visit_date'] = [loc_visitDate]
      else: dict_obsDate[ip]['local_visit_date'].append( loc_visitDate )

  return dict_obsDate

log_file = 'sitools-log-service.log_cat_szdbv2' #'sitools-log-service.log_cat_oldnew' # sitools-log-service.log_cat_oldnew # sitools-log-service.log_test
print '\n- Reading the file %s ...\n' % log_file
log = asciidata.open(log_file, delimiter='\t') 

log_datetime = [item.split(' - ')[0] for item in (log[0]) ]
parsed_dates = [parser.parse(item) for item in log_datetime] # Parse (datetimes)
print '\n- Start log: %s\n- End log: %s\n' % (log_datetime[0], log_datetime[-1])

log_ip = [str(item) for item in (log[2]) ]
ip2exclude = ["129.175.64.124", "129.175.65.119", "129.175.64.65", "129.175.67.137",
	      "129.175.64.230", "172.18.60.17", "129.175.65.131", "129.175.65.82",
	      "129.175.66.42", "127.0.0.1", "129.175.66.43", "129.175.66.248", "129.175.68.20",
              "129.175.64.25", '82.227.158.245', '82.230.111.189', '128.78.210.125', 
              '129.175.65.115', '129.175.127.172','129.175.64.209', 'unknown']
#List of Bot ID
bot  = ['drupal', 'libwww-perl', 'googlebot','mj12bot', 'spider', 'fetcher', 'blogtrottr']


ip_good = []
dict_ip_good = {}

idxs_ip_good = []


for i, item in enumerate(log[14]):
  
  ip_tmp = log_ip[i]
  
  #Excluded from 'good_ip':
  #- Robots
  #- Internal IP (IAS, idc)
  #- Consecutive visits from the same IP
  #- Visits from the same IP within 10 minutes
  
  if [bot_elem for bot_elem in bot if bot_elem in item.lower()] or ('robot' in log[7][i]) or (ip_tmp in ip2exclude) or ('.'.join(ip_tmp.split('.')[:2]) in ['220.181', '123.125'] ):
    pass
  else:    
    if i>0 and (ip_tmp != log_ip[i-1]):  
      if ip_tmp not in dict_ip_good:
	dict_ip_good[ip_tmp] = {}
	dict_ip_good[ip_tmp]['visit_date'] = [ parsed_dates[i] ]
	ip_good.append(log_ip[i])
	idxs_ip_good.append(i)
      else:
	if (parsed_dates[i]-dict_ip_good[ip_tmp]['visit_date'][-1]).total_seconds() > 600:
	  dict_ip_good[ip_tmp]['visit_date'].append( parsed_dates[i] )
	  ip_good.append(log_ip[i])
	  idxs_ip_good.append(i)
	  

dict_city = {}

for item in Counter(ip_good).keys():
  url = 'http://www.telize.com/geoip/'+item  #http://www.freegeoip.net/json/ #http://www.telize.com/geoip/
  response = urllib.urlopen(url)
  json_output = response.read()
  json.loads(json_output)
  data = json.loads(json_output)

  try:
    lat_ip = data['latitude']
  except:
    lat_ip = 0
    
  try:
    lon_ip = data['longitude']
  except:
    lon_ip = 0
  
  try:
    country = data['country'] #country_name
  except:
    country = ''
  
  try:
    city    =  data['city'] 
  except:
    city    = ''
  
  
  if 'lat' not in dict_ip_good[item]:
    dict_ip_good[item]['lat'] = [ lat_ip ]
    dict_ip_good[item]['lon'] = [ lon_ip ]
  else:
    dict_ip_good[item]['lat'].append( lat_ip )
    dict_ip_good[item]['lon'].append( lon_ip )

  ##Exclude non-standard characteres
  #if re.match("^[a-zA-Z0-9_]*$", country): pass
  #else:
    #for ch in country:
      #if re.match("^[a-zA-Z0-9_]*$", ch): pass
      #else: country= re.sub(ch, '',country)

  #if re.match("^[a-zA-Z0-9_]*$", city): pass
  #else:
    #for ch in city:
      #if re.match("^[a-zA-Z0-9_]*$", ch): pass
      #else: city= re.sub(ch, '',city)
  
  if lat_ip == 0 and lon_ip == 0:
    #Exclude unknown IPs
    print 'Unknown Position for IP: %s - skipped' % item
  else:
    print '%s,%s,%s,%s,%s,%s' % (item,lat_ip, lon_ip,country, city,Counter(ip_good)[item])
    key = city+" - "+country
    if (key in dict_city) and key != ' - ':
      dict_city[key]['visits'] += Counter(ip_good)[item]
      dict_city[key]['IP'].append(item)
    
    elif key == ' - ':
      if item in dict_city:
	dict_city[item]['visits'] += Counter(ip_good)[item]
	dict_city[item]['IP'].append(item)
      else:
	dict_city[item] = {}
	dict_city[item]['visits'] = Counter(ip_good)[item]
	dict_city[item]['IP'] = [item]
	dict_city[item]['lat_ip'] = lat_ip
	dict_city[item]['lon_ip'] = lon_ip
	dict_city[item]['country'] = ''
	
    else:
      dict_city[key] = {}
      dict_city[key]['visits'] = Counter(ip_good)[item]
      dict_city[key]['IP'] = [item]
      dict_city[key]['lat_ip'] = lat_ip
      dict_city[key]['lon_ip'] = lon_ip
      dict_city[key]['country'] = country
    

#Date analysis
date_good = []

visits = {}
for item in dict_city: visits[item] = dict_city[item]['visits']

#Visitors sorted by number of visits
sorted_visitors = sorted(visits.items(), key=operator.itemgetter(1), reverse = True)

#The 5 most frequent visitors
top_visitors = sorted_visitors[:5]
date_1st_visitor, date_2nd_visitor, date_3rd_visitor, date_4th_visitor, date_5th_visitor = [],[],[],[],[]

#date_beijing, date_sandy, date_bonn, date_moscow, date_cambrUSA = [],[],[],[],[]

'''
for item in dict_ip_good : 
    for date in dict_ip_good[item]['visit_date']: 
      date_good.append(date)
      if item in dict_city['Beijing - China']['IP']: date_beijing.append(date)
      elif item in dict_city['Sandy City - United States']['IP'] : date_sandy.append(date) 
      elif item in dict_city['Bonn - Germany']['IP'] : date_bonn.append(date)
      elif item in dict_city[' - Russia']['IP'] : date_moscow.append(date)
      elif item in dict_city['Cambridge - United States']['IP'] : date_cambrUSA.append(date)
'''

#Record the visit dates of the top 5 visitors
for item in dict_ip_good : 
    for date in dict_ip_good[item]['visit_date']: 
      date_good.append(date)
      if   item in dict_city[top_visitors[0][0]]['IP'] : date_1st_visitor.append(date)
      elif item in dict_city[top_visitors[1][0]]['IP'] : date_2nd_visitor.append(date) 
      elif item in dict_city[top_visitors[2][0]]['IP'] : date_3rd_visitor.append(date)
      elif item in dict_city[top_visitors[3][0]]['IP'] : date_4th_visitor.append(date)
      elif item in dict_city[top_visitors[4][0]]['IP'] : date_5th_visitor.append(date)


#Convert datetime dates into floats
date_good_num = map(lambda x: matplotlib.dates.date2num(x), date_good) # == date_num = matplotlib.dates.date2num(date_good)

t_min = min( date_good )
t_max = max( date_good )
dt = 1# 1 days

#Get the bins ffrom the hist, for the plots and count in each bin date
bins4hist, bins4plot, cnts = hist_date(date_good,t_min, t_max, dt)

#plt.grid()
#plt.plot_date(bins4hist, cnts, fmt='k-')


#hist_bins = np.arange(0,21,1) #(9,21,1)

'''
bins4hist, bins4plot, cnt_beijing = hist_date(date_beijing,t_min, t_max, dt)
bins4hist, bins4plot, cnt_sandy = hist_date(date_sandy,t_min, t_max, dt)
bins4hist, bins4plot, cnt_bonn = hist_date(date_bonn,t_min, t_max, dt)
bins4hist, bins4plot, cnt_moscow = hist_date(date_moscow,t_min, t_max, dt)
bins4hist, bins4plot, cnt_cambrUSA = hist_date(date_cambrUSA,t_min, t_max, dt)
'''

bins4hist, bins4plot, cnt_1st = hist_date(date_1st_visitor, t_min, t_max, dt)
bins4hist, bins4plot, cnt_2nd = hist_date(date_2nd_visitor, t_min, t_max, dt)
bins4hist, bins4plot, cnt_3rd = hist_date(date_3rd_visitor, t_min, t_max, dt)
bins4hist, bins4plot, cnt_4th = hist_date(date_4th_visitor, t_min, t_max, dt)
bins4hist, bins4plot, cnt_5th = hist_date(date_5th_visitor, t_min, t_max, dt)


# -->>>>
ax = plt.subplot(111)
plt.title('Visits to SZ-DB')
plt.xlabel('Time of visit')
plt.ylabel('Num. of visits / day')

tot = ax.bar(bins4plot, cnts, width=0.95, color='black',linewidth=0, alpha = 0.2)

dt_barShift = 0.15
width=0.15

'''
rects1 = ax.bar(bins4plot,cnt_beijing, width=width, color='red') # bins_beijing
bins_shift = [x+1*dt_barShift for x in bins4plot]; rects2 = ax.bar(bins_shift, cnt_sandy, width=width, color='blue')
bins_shift = [x+2*dt_barShift for x in bins4plot]; rects3 = ax.bar(bins_shift, cnt_bonn, width=width, color='yellow')
bins_shift = [x+3*dt_barShift for x in bins4plot]; rects4 = ax.bar(bins_shift, cnt_moscow, width=width, color='brown')
bins_shift = [x+4*dt_barShift for x in bins4plot]; rects5 = ax.bar(bins_shift, cnt_cambrUSA, width=width, color='cyan')
'''

rects1                                                    = ax.bar(bins4plot,  cnt_1st, width=width, color='red') # bins_beijing
bins_shift = [x+1*dt_barShift for x in bins4plot]; rects2 = ax.bar(bins_shift, cnt_2nd, width=width, color='blue')
bins_shift = [x+2*dt_barShift for x in bins4plot]; rects3 = ax.bar(bins_shift, cnt_3rd, width=width, color='yellow')
bins_shift = [x+3*dt_barShift for x in bins4plot]; rects4 = ax.bar(bins_shift, cnt_4th, width=width, color='green')
bins_shift = [x+4*dt_barShift for x in bins4plot]; rects5 = ax.bar(bins_shift, cnt_5th, width=width, color='cyan')



#Start of new instance
x = datetime.datetime(2015,03,12,16,00,00)
x = [x,x] ; y = [0,50]
plt.plot_date(x,y, 'k--'); 
x = datetime.datetime(2015,03,12,16,00,00); x = [x,x]
plt.text(x[0],1.09*y[1], 'New SZ-DB online', horizontalalignment='center'); plt.text(x[0],1.03*y[1], '(12/03/2015 - 16:00)', horizontalalignment='center')

'''
ax.legend( (tot, rects1[0], rects2[0],rects3[0], rects4[0],rects5[0]), ('Total', 'Beijing', 'Sandy City (USA)','Bonn', 'Moscow','Cambridge (USA)'), loc='upper left' )
'''

ax.legend( (tot, rects1[0], rects2[0],rects3[0], rects4[0],rects5[0]), ('Total', '%s (tot. visits: %s)' % ( top_visitors[0][0], top_visitors[0][1] ), '%s (tot. visits: %s)' % ( top_visitors[1][0], top_visitors[1][1]), '%s (tot. visits: %s)' % ( top_visitors[2][0], top_visitors[2][1] ), '%s (tot. visits: %s)' % ( top_visitors[3][0], top_visitors[3][1]), '%s (tot. visits: %s)' % ( top_visitors[4][0], top_visitors[4][1] )), loc='upper left' )

#bin4hist_dates = matplotlib.dates.num2date(bins4hist)
ax.grid()
ax.xaxis_date()

#plt.savefig('szdb_visits_hist.png', bbox_inches='tight')
plt.show()

# <<<<--
'''
dict_ip_good_localTime = get_gmtOffset(dict_ip_good)
loc_visitDates = [x for ip in dict_ip_good_localTime for x in dict_ip_good_localTime[ip]['local_visit_date'] if ip not in dict_city['Beijing - China']['IP'] ]
hist_weekday_hours(loc_visitDates, 0, 'ALL_but_China.png')
hist_weekday_hours(date_sandy, -7, 'sandy.png')
#hist_weekday_hours(date_moscow, 2, 'moskow.png')
hist_weekday_hours(date_cambrUSA, -5, 'cambridge_usa.png')
hist_weekday_hours(date_bonn, 0, 'bonn.png')
hist_weekday_hours(date_beijing, +6, 'china.png')
'''

dict_ip_good_localTime = get_gmtOffset(dict_ip_good)
loc_visitDates = [x for ip in dict_ip_good_localTime for x in dict_ip_good_localTime[ip]['local_visit_date'] ] # if ip not in dict_city['Beijing - China']['IP']

hist_weekday_hours(loc_visitDates, 0, 'ALL_but_China.png')

#get the GMT offset for the first 5 visitors
gmtOffset_top5 = []

for item in top_visitors:
  ip_item = dict_city[item[0]]['IP'][0] # Take just the first IP of the item
  print item, ip_item, dict_ip_good_localTime[ ip_item ]['gmtOffset'] -1
  gmtOffset_top5.append( dict_ip_good_localTime[ ip_item ]['gmtOffset'] - 1 )

hist_weekday_hours(date_1st_visitor, gmtOffset_top5[0], top_visitors[0][0]+'.png')
#hist_weekday_hours(date_moscow, 2, 'moskow.png')
hist_weekday_hours(date_2nd_visitor, gmtOffset_top5[1], top_visitors[1][0]+'.png')
hist_weekday_hours(date_3rd_visitor, gmtOffset_top5[2], top_visitors[2][0]+'.png')
hist_weekday_hours(date_4th_visitor, gmtOffset_top5[3], top_visitors[3][0]+'.png')
hist_weekday_hours(date_5th_visitor, gmtOffset_top5[4], top_visitors[4][0]+'.png')
