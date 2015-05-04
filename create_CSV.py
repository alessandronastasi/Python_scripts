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
This script creates a CSV file starting from a FITS table.

The syntax:

$ python create_CSV.py <table>.fits

will generate the file <table>.csv

@author: Alessandro NASTASI
@date: 04/05/2015
'''
__author__ = "Alessandro Nastasi"
__credits__ = ["Alessandro Nastasi"]
__license__ = "GPL"
__version__ = "1.0"
__date__ = "04/05/2015"

import sys, io, os
import pyfits
import numpy as np

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

if (len(sys.argv) > 1):
    fits_file = sys.argv[1] 
else:
    print bcolors.WARNING +  "\n\tSintax:\t$ python create_CSV.py <table>.fits \n" + bcolors.ENDC
    os._exit(0)

fileName = fits_file.split('.')[0]

fits_file = pyfits.open(fits_file)

data = fits_file[1].data

keywords = data.names
nRows = data.size

output_file = open(fileName+'.csv', 'w')

towrite = ''
for key in keywords[:-1]: towrite+=str(key)+','
towrite+= keywords[-1]+'\n'

output_file.write(towrite)
towrite = ''

for j in range(nRows):
	for key in keywords[:-1]:
		towrite += str(data[key][j])+','
        towrite+= str(data[keywords[-1]][j])+'\n'
	output_file.write(towrite)
	towrite = ''

print "\n\t>> Generated the CSV file:" + bcolors.OKGREEN + " %s \n" % (fileName+'.csv') + bcolors.ENDC

