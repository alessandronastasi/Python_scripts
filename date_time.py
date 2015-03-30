#!/usr/bin/python
'''
Functions handling datetime vectors and producing histograms in bins of
- days
- weekdays
- daytime

In addition, the timezones offsets are handled as well by the function get_gmtOffset()
'''

def hist_days(date_vector, lim_inf, lim_sup, dt = 1): # Default = 1day bin
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


def hist_weekday_hours(date_vector, time_shift = 0, plot_name = 'plot.png'): # Default time_shift = 0: local time = observed time
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
  weekday_label = 'LOCAL weekday of visit'
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
  '''
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
    data = json.loads(response.read())
    
    gmtOffset = data['gmtOffset']

    dict_obsDate[ip]['gmtOffset'] = gmtOffset
    
    #loop on the visit dates
    for i, dates in enumerate(dict_obsDate[ip]['visit_date']):
      loc_visitDate = dates + datetime.timedelta(hours = int(gmtOffset - 1) )
      if i == 0: dict_obsDate[ip]['local_visit_date'] = [loc_visitDate]
      else: dict_obsDate[ip]['local_visit_date'].append( loc_visitDate )

  return dict_obsDate
