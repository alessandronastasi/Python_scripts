#!/usr/bin/python

import pyfits
import numpy as np
import os, sys, re, time

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

if (len(sys.argv) > 1):
    filename1 = sys.argv[1]
    filename2 = sys.argv[2] 
else:
    print bcolors.WARNING +  "\n\tSintax:\t$ python compare_FITS.py <fits_file_1> <fits_file_2>\n" + bcolors.ENDC
    os._exit(0)

fits1 = pyfits.open(filename1)
fits2 = pyfits.open(filename2)

max_length = max(len(filename1), len(filename2)) 
formatting = '{0:<%ss}' % (max_length+5)

try:
  creation_date1 = fits1[0].header['DATE']
  creation_date2 = fits2[0].header['DATE']
  
  max_length = max(len(creation_date1), len(creation_date2)) 
  formatting += '{0:^%ss}' % (max_length+5)

    #print '\n> Creation dates do not match:'
  #if creation_date1 != creation_date2: 
  #else:
    #print '\n> Creation dates match:'
  print '\n- %s created on %s\n- %s created on %s' % (filename1, creation_date1, filename2, creation_date2)
except:
  pass
    
Nrows1 = fits1[1].header['NAXIS2']
Ncol1 = fits1[1].header['TFIELDS']

Nrows2 = fits2[1].header['NAXIS2']
Ncol2 = fits2[1].header['TFIELDS']

max_length = max(len(str(Nrows1)), len(str(Ncol1)), len(str(Nrows2)), len(str(Ncol2))) 
formatting += '{0:^%ss}' % (max_length+5)

print '\nFile Name\tNum Rows\tNum Col\n%s\t%s\t%s\n%s\t%s\t%s' % (filename1,Nrows1,Ncol1,filename2,Nrows2,Ncol2)

try:
  comment1 = fits1[0].header['COMMENT']
  comment2 = fits2[0].header['COMMENT']
  
  if comment1 != comment2: 
    print '\n> Header comments do not match:\n\t- comment in %s:\n"%s"\n\t- comment in %s:\n"%s"' % (filename1, comment1, filename2, comment2)
except:
  pass

data1 = fits1[1].data
data2 = fits2[1].data

#Check fields names and format
if data1.names != data2.names: 
  print '\n> Different field names: \n\t- file1: %s\n\t- file2: %s' % (data1.names, data2.names)

if data1.formats != data2.formats: 
  print '\n> Different field formats: \n\t- file1: %s\n\t- file2: %s' % (data1.formats, data2.formats)

report_file = open('difference_summary.tab', 'w')

if (Nrows1 == Nrows2) and (Ncol1 == Ncol2) and (data1.names == data2.names) and (data1.formats == data2.formats):
  max_name_length = max([len(name) for name in data1.names])
  formatting = '{0:<%ss}- {1:<%ss}{2:<7s}' % (len(str(Ncol1))+1, max_name_length+5)
  print '\n> Checking the values of the %s fields ...' % Ncol1
  for k, name in enumerate(data1.names):
    toWrite = ''
    check_column = True
    idx_differences = []
    values = []
    for i in range(data1.size):
      if data1[name][i] != data2[name][i] and (str(data1[name][i]) != 'nan' and str(data2[name][i]) != 'nan'):
	idx_differences.append(i)
	#print data1[name][i],"->", data2[name][i]
    if len(idx_differences) > 0:
      print formatting.format(str(k+1), name, bcolors.FAIL+'[FAIL]'+bcolors.ENDC )
      toWrite += formatting.format(str(k+1), name, '[FAIL]')
      #print bcolors.WARNING+"\n  --> Found %s differences at rows: %s (%s -> %s)\n" % (len(idx_differences), idx_differences, data1[name][idx_differences] , data2[name][idx_differences])+bcolors.ENDC
      for j in idx_differences:
	#print bcolors.WARNING+"%s -> %s" % (data1[name][j] , data2[name][j])+bcolors.ENDC
	toWrite += "\n%s -> %s" % (data1[name][j] , data2[name][j])
    else:
      print formatting.format(str(k+1), name, bcolors.OKGREEN+'[OK]'+bcolors.ENDC )
      toWrite += formatting.format(str(k+1), name, '[OK]' )
     
    report_file.write(toWrite+'\n')

report_file.close()    

print "\n\t> A detailed list of found differences is reported in "+bcolors.OKBLUE+"'difference_summary.tab'"+bcolors.ENDC+"\n\n"
