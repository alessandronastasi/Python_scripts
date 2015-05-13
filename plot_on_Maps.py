#!/usr/bin/python
# ******************************************************************************
#    Copyright 2015 - Alessandro Nastasi
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
This script generates an HTML file where the number and locations of the IP visits 
are plotted on Google Maps.
@author: Alessandro NASTASI
@date: 13/05/2015
'''
__author__ = "Alessandro Nastasi"
__credits__ = ["Alessandro Nastasi"]
__license__ = "GPL"
__version__ = "1.0"
__date__ = "13/05/2015"

html_body = """
<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no">
    <meta charset="utf-8">
    <title>Heatmaps</title>
    <style>
      html, body, #map-canvas {
        height: 100%%;
        margin: 0px;
        padding: 0px
      }
      #panel {
        position: absolute;
        top: 5px;
        left: 50%%;
        margin-left: -180px;
        z-index: 5;
        background-color: #fff;
        padding: 5px;
        border: 1px solid #999;
      }
    </style>
    <script src="https://maps.googleapis.com/maps/api/js?v=3.exp&signed_in=true&libraries=visualization&sensor=true"></script>

    <script>
    
// This example creates circles on the map, representing
// populations in North America.

// First, create an object containing LatLng and population for each city.
var citymap = {};

%(MARKERS_DEFINITION)s

var cityCircle;
var map, heatmap;

var ipData = [

%(HEATMAP_DEFINITION)s

];

function initialize() {
  // Create the map.
  var mapOptions = {
    zoom: 5,
    center: new google.maps.LatLng(48.667, 2.117),
    mapTypeId: google.maps.MapTypeId.SATELLITE//TERRAIN
  };

  var map = new google.maps.Map(document.getElementById('map-canvas'),
      mapOptions);

  // Construct the icon for each value in citymap.
  // Note: We scale the area of the circle based on the population.
  for (var city in citymap) {
    var contentString = citymap[city].title+' ('+citymap[city].city+')'+': '+citymap[city].visits;
    var populationOptions = {
      map: map,
      position: citymap[city].center,
      title: contentString, //citymap[city].title,
      icon: 'http://szcluster-db.ias.u-psud.fr/sitools/upload/locMarker_redCircle.gif',
    };
    
    // Add the circle for this city to the map.
    cityCircle = new google.maps.Marker(populationOptions); //Marker
    
  }
  var pointArray = new google.maps.MVCArray(ipData);

  heatmap = new google.maps.visualization.HeatmapLayer({
    data: pointArray,
    dissipating: 1,
    opacity: 1,
    maxIntensity:20,
    radius: 30
  });

  heatmap.setMap(map);

}

function toggleHeatmap() {
  heatmap.setMap(heatmap.getMap() ? null : map);
}

function changeGradient() {
  var gradient = [
    'rgba(0, 255, 255, 0)',
    'rgba(0, 255, 255, 1)',
    'rgba(0, 191, 255, 1)',
    'rgba(0, 127, 255, 1)',
    'rgba(0, 63, 255, 1)',
    'rgba(0, 0, 255, 1)',
    'rgba(0, 0, 223, 1)',
    'rgba(0, 0, 191, 1)',
    'rgba(0, 0, 159, 1)',
    'rgba(0, 0, 127, 1)',
    'rgba(63, 0, 91, 1)',
    'rgba(127, 0, 63, 1)',
    'rgba(191, 0, 31, 1)',
    'rgba(255, 0, 0, 1)'
  ]
  heatmap.set('gradient', heatmap.get('gradient') ? null : gradient);
}

function changeRadius() {
  heatmap.set('radius', heatmap.get('radius') ? null : 35);
}

function changeOpacity() {
  heatmap.set('opacity', heatmap.get('opacity') ? null : 1);
}

function changemaxIntensity() {
  heatmap.set('maxIntensity', heatmap.get('maxIntensity') ? null : 20);
}

google.maps.event.addDomListener(window, 'load', initialize);

    </script>
  </head>
  <body>
      <div id="panel">
      <button onclick="toggleHeatmap()">Toggle Heatmap</button>
      <button onclick="changeGradient()">Change gradient</button>
      <button onclick="changeRadius()">Change radius</button>
      <button onclick="changeOpacity()">Change opacity</button>
      <button onclick="changemaxIntensity()">Change Max Intensity</button>
    </div>

    <div id="map-canvas"></div>
  </body>
</html>
"""

import sys,os, re
import struct, socket
from pandas import read_csv
import matplotlib.pyplot as plt
import matplotlib.dates
import numpy as np
import asciidata

from dateutil import parser

import urllib, json
from collections import Counter 

def ip2long(ip):
    """
    Convert an IP string to long
    """
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]

'''
ipstr = raw_input("Enter IP: ")
'''

def locate_ip(ipstr, blocks, location):
  ipL = int(ip2long(ipstr))

  print "ipL: ", ipL

  #location = read_csv('./GeoLiteCity_20150303/GeoLiteCity-Location.csv')
  #blocks = read_csv('./GeoLiteCity_20150303/GeoLiteCity-Blocks.csv')

  startIpNum = [int(item) for item in blocks['startIpNum'] ]
  endIpNum = [int(item) for item in blocks['endIpNum'] ]

  tmp = ''
  for i,item in enumerate(blocks['locId']):
      if ipL >= startIpNum[i] and ipL <= endIpNum[i]: print 'Loc ID:', item; tmp = str(item); break
      else:
	if i == len(blocks['locId'])-1: print "IP not found! Exit."; os._exit(0)

  lat = [float(item) for item in location['latitude'] ]
  lon = [float(item) for item in location['longitude'] ]
  country = [item for item in location['country'] ]
  region = [item for item in location['region'] ]
  postcode = [item for item in location['postalCode'] ]

  lon_ip = 0.0
  lat_ip = 0.0

  for i, loc in enumerate(location['locId']):
    if str(loc) == tmp: print "Lat: %s , Lon: %s, Country: %s, Region : %s , Postal Code: %s" % (lat[i], lon[i], country[i], region[i], postcode[i]); lat_ip = lat[i]; lon_ip = lon[i]; break
    else:
      if i == len(location['locId'])-1: print "POSITION not found! Exit."; os._exit(0)

  return lon_ip, lat_ip

#TEST SZ-DB statistics
html_prefix = 'NEW-' #'TEST-'
log_file = 'sitools-log-service.log_cat_szdbv2' #'sitools-log-service.log_cat_oldnew' # sitools-log-service.log_cat_oldnew # sitools-log-service.log_test
print '\n- Reading the file %s ...\n' % log_file

log = asciidata.open(log_file, delimiter='\t')

#OLD SZ-DB statistics
#html_prefix = 'OLD-'
#log = asciidata.open('sitools-log-service.log.0', delimiter='\t')

#NEW SZ-DB statistics
#html_prefix = 'NEW-'
#log = asciidata.open('sitools-log-service.log_cat_szdbv2', delimiter='\t')

#log_time = [item for item in (log[1]) ]
log_datetime = [item.split(' - ')[0] for item in (log[0]) ]
parsed_dates = [parser.parse(item) for item in log_datetime] # Parse (datetimes)
num_dates = [matplotlib.dates.date2num(item) for item in parsed_dates] # Convert type(datetime) -> number

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
  
  if [bot_elem for bot_elem in bot if bot_elem in item.lower()] or ('robot' in log[7][i]) or (ip_tmp in ip2exclude):
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
	  

print Counter(ip_good)

html_name = html_prefix+'szdb_visits_Maps.html'
fileHtmlOutput = open(html_name, 'w')
heatmap_vector = ''

dict_city = {}

#Generate CIRCLE markers and HeatMap

for item in Counter(ip_good).keys():
  url = 'http://www.telize.com/geoip/'+item #http://www.freegeoip.net/json/
  try:
    response = urllib.urlopen(url)
    data = json.loads(response.read())
  except:
    print "\n!! Error with JSON data from IP:%s - Response:%s" % (item, response)

  try:
    lat_ip = data['latitude']
  except:
    lat_ip = ''
    
  try:
    lon_ip = data['longitude']
  except:
    lon_ip = ''
  
  try:
    country = data['country'] #country_name
  except:
    country = ''
  
  try:
    city    =  data['city'] 
  except:
    city    = ''

  #Exclude non-standard characteres
  if re.match("^[a-zA-Z0-9_]*$", country): pass
  else:
    for ch in country:
      if re.match("^[a-zA-Z0-9_]*$", ch): pass
      else: country= re.sub(ch, '',country)

  if re.match("^[a-zA-Z0-9_]*$", city): pass
  else:
    for ch in city:
      if re.match("^[a-zA-Z0-9_]*$", ch): pass
      else: city= re.sub(ch, '',city)
  
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
    
    for j in range(Counter(ip_good)[item]):
      if lat_ip and lon_ip:
	heatmap_vector +="\n  new google.maps.LatLng(%s,%s)," % (lat_ip, lon_ip)


#Define MARKERS according to DICT_CITY
circle_marker = ''

for item in dict_city:
  if dict_city[item]['lat_ip'] and dict_city[item]['lon_ip']:
    circle_marker +="\ncitymap['%s'] = {" % item
    circle_marker +="\n  title: '%s'," % str(dict_city[item]['IP']).replace("'",'')
    circle_marker +="\n  center: new google.maps.LatLng(%s, %s)," % (dict_city[item]['lat_ip'], dict_city[item]['lon_ip'])
    circle_marker +="\n  visits: %s," % dict_city[item]['visits']
    circle_marker +="\n  city: '%s'," % item
    circle_marker +="\n  country: '%s'" % dict_city[item]['country']
    circle_marker +="\n};"

    

html_final = html_body % {
  'MARKERS_DEFINITION': circle_marker,
  'HEATMAP_DEFINITION': heatmap_vector 
  }
  
fileHtmlOutput.write(html_final)
fileHtmlOutput.close()
