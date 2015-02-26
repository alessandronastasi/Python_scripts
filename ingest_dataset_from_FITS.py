#!/usr/bin/python
"""
This script writes/updates a table into a a PostgreSQL Database 
(dafault is 'DATABASE_NAME') reading data and columns formats directly 
from a FITS file. 
The database can be local or defined on a server (default is 'idc-db1').

Syntax:

$ python ingest_dataset_from_FITS.py <file>.fits

@author: Alessandro NASTASI - 26-02-2015
"""

import psycopg2
import pyfits
#from pandas import read_csv

import numpy as np
import os, sys, re, math
from time import time

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

PSQL_FORMAT = {
  'L' : 'boolean DEFAULT false',
  #'X':  '',   #bit                            
  #'B':  '',   #Unsigned byte                  
  'I' : 'integer DEFAULT (-1) NOT NULL',
  'J' : 'real DEFAULT (- (1.6375E+30::numeric)::real)',
  'K' : 'real DEFAULT (- (1.6375E+30::numeric)::real)',
  'E' : 'real DEFAULT (- (1.6375E+30::numeric)::real)',
  'D' : 'real DEFAULT (- (1.6375E+30::numeric)::real)',
  'A' : 'character varying(1027)' # % fits_format.split(char)[0],
  #'C' :  '', #single precision complex       
  #'M': psql_format =  '', #double precision complex       
  #'P': psql_format =  '', #array descriptor               
  #'Q': psql_format =  ''  #array descriptor               
  }

def convert_into_SQL_format(fits_format):
  formats = 'LXBIJKAEDCMPQ'
  psql_format = ''
  for char in formats:
    if len(fits_format.split(char)) > 1:
      psql_format = PSQL_FORMAT[char]      
  return psql_format

def RADECtoXYZ(RA,DEC):
  """Convert RA DEC pointing to X Y Z"""
  #convert degrees to radians
  RArad=math.radians(RA)
  DECrad=math.radians(DEC)
  X=math.cos(DECrad)*math.cos(RArad)
  Y=math.cos(DECrad)*math.sin(RArad)
  Z=math.sin(DECrad)
  ResultXYZ=[X,Y,Z]
  return ResultXYZ 

dbname = "'DATABASE_NAME'"	#<--- Customize here

if (len(sys.argv) > 1):
    filename = sys.argv[1] 
else:
    print bcolors.WARNING +  "\n\tSintax:\t$ python ingest_dataset_from_FITS.py <file>.fits\n" + bcolors.ENDC
    os._exit(0)

host = raw_input("\n> Where is the dataset to update/create? (enter 0 to exit)\n\t- localhost [1]\n\t- on the server "+bcolors.WARNING+'idc-db1'+bcolors.ENDC+" [2]\n\t--> ")
choice = False

while not choice:
  if host=='1':
    #LOCALHOST
    user = "'postgres'"
    host = "'localhost'"
    pwd = "''"
    choice = True
      
  elif host=='2':
    #IDC-DB1
    user = "'username'"  #<--- Customize here
    host = "'idc-db1'"	 #<--- Customize here
    pwd = "''"
    choice = True
    
  elif host=='0':
    print '\nExit.\n'; os._exit(0)
    
  else: 
    print bcolors.WARNING+'\n!! Choice not valid !!'+ bcolors.ENDC
    host = raw_input('\n\t> Please enter 1, 2 or 0: ')
    
fileInput = pyfits.open(filename)    
fileExtension = filename.split('.')[1].strip()

input_mode = 'fits' #''None'

#CSV mode not yet implemented...
'''
if fileExtension == 'fits': input_mode = 'fits'
else: input_mode = 'csv'
'''

dataset = raw_input('\n> Please enter the name of the new dataset to create into the %s database: ' % dbname)

#Connection do the database
conn = psycopg2.connect("dbname="+dbname+" user="+user+" host="+host+" password="+pwd+"")

#Create the Psycopg object
cur = conn.cursor()

# *** Read the columns to INSERT INTO the table ***

start = time() #Just to monitor the execution time

if input_mode == 'fits':
  print '\n- Reading/storing data from FITS table (it may take some time. Please wait...)'
  data = fileInput[1].data
  
  table_size = data.size # 100 joined = 210 extractednames
  
  fields = (data.names)
  fields_format = (data.formats)
  data2D = [[data[field][i] for field in fields] for i in range(table_size)] #Storing all in a 2D array, but without the name line

# *************************************************

#Create a TABLE 
table = False

#First test if the table already exists:
cur.execute("select exists(select * from information_schema.tables where table_name=%s)", (dataset,))
table = cur.fetchone()[0]
drop_cascade = 'n'
#if yes, drop the table
if table:
  print '\n- Dataset already exists. Dropping it...'
  try:
    cur.execute("DROP TABLE "+dataset+";")
  except:
    #If the dataset has one or more associated VIEWs, *everything* must be dropped
    print bcolors.WARNING+"\n>> Impossible to drop the table, possibly because other elements (e.g. VIEWS) depend on it. <<"+bcolors.ENDC
    drop_cascade = raw_input("\n\t> Do you want to use the 'DROP ... CASCADE' option to delete them too? [y/n]: ")
    if drop_cascade in 'YESyes1':
      #A re-connection is necessary if the DROP test failed
      conn = psycopg2.connect("dbname="+dbname+" user="+user+" host="+host+" password="+pwd+"")
      cur = conn.cursor()
      cur.execute("DROP TABLE "+dataset+" CASCADE;")
      print '\n\t- Dataset '+bcolors.OKGREEN+"'%s'" % dataset +bcolors.ENDC+' and all his dependencies successfully dropped.'
    else:
      print "\n- Exit.\n"; os._exit(0)
      
else:
  #If not, just create a new one
  print '\n- Table does not exist. A new one will be created...'

#If 'RA' and 'DEC' are found, the Cartesian coordinates x,y,z are computed and automatically appended at the end of the table
if ('RA' in fields) and ('DEC' in fields):
  print '\n- Found RA and DEC. The Cartesian coordinates x,y,z will be computed and appended to the dataset as additional columns...'
  fields.extend(['x','y','z'])
  fields_format.extend(['E','E','E'])
  xyz = [RADECtoXYZ(data['RA'][j], data['DEC'][j]) for j in range(len(data2D))]
  data2D = np.column_stack( [ data2D , xyz ] )

#Store the info about which fields are string
fields_string_length = [len(field.split('A')) for field in fields_format]

print '\n- Creating/updating the table...\n'
createTable_cmd = "CREATE TABLE %s (id integer PRIMARY KEY" % dataset
for j, name in enumerate(fields):
  
  createTable_cmd += ", %s %s" % (name, convert_into_SQL_format(fields_format[j]) )
  
createTable_cmd +=");"
cur.execute(createTable_cmd)

#Fill in the columns
for i in range(table_size):
  sys.stdout.write("- Filling the table...%s%%\r" % (int(100*(i/(1.0*table_size))) ) )
  sys.stdout.flush()
  toExecute = "INSERT INTO %s (id " % dataset
  for field in fields: toExecute += ", %s" % field
  toExecute += ") VALUES (%s " % i
  for j, field in enumerate(fields):

    if fields_string_length[j]>1:
      if str(data2D[i][j]) == '-': 	toExecute += ", NULL"
      else:				toExecute += ", '%s'" % data2D[i][j]
    else:
      if str(data2D[i][j]) == 'nan': toExecute += ", NULL"
      else: toExecute += ", %s" % data2D[i][j]

  toExecute +=")"
  cur.execute(toExecute)
  if i == table_size-1: sys.stdout.write("- Filling the table...100% - "+bcolors.OKGREEN+"[OK]"+bcolors.ENDC+"\r")
stop = time()

delta_t = stop-start; print '\n\n< time: %s sec >' % delta_t

#Apply the changes -> create the actual database
conn.commit()

#Close the connections
cur.close()
conn.close()

print "\n--> The dataset "+bcolors.OKGREEN+"'%s'" % dataset+bcolors.ENDC+" has been updated/created into the "+bcolors.OKBLUE+dbname+bcolors.ENDC+" database in host: "+bcolors.OKBLUE+host+bcolors.ENDC+".\n"
