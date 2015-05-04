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
This script creates a fits table starting from an ASCII file.
IMPORTANT: the first line of the file must contain the names 
of the labels and has to be UNCOMMENTED.  		

The syntax is:

$ python create_FITS.py <ascii_file> <table>.fits

@author: Alessandro NASTASI for IAS - IDOC 
@date: 04/05/2015
'''
__author__ = "Alessandro Nastasi"
__credits__ = ["Alessandro Nastasi"]
__license__ = "GPL"
__version__ = "1.0"
__date__ = "04/05/2015"

import numpy as np
import os, sys, re
import asciidata
import pyfits
from astLib import astCoords
from datetime import date

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

_FIELDS_DICTIONARY = {

  'INDEX': { 'format': 'I', 'unit': 'None' },
  
  # ****** ACT ******
  'INDEX_ACT': { 'format': 'I', 'unit': 'None' },
  'CATALOG': { 'format': '7A', 'unit': 'None' },
  #'NAME': { 'format': '18A', 'unit': 'None' },
  #'GLON': { 'format': 'E', 'unit': 'degrees' },
  #'GLAT': { 'format': 'E', 'unit': 'degrees' },
  #'RA': { 'format': 'E', 'unit': 'degrees' },
  #'DEC': { 'format': 'E', 'unit': 'degrees' },
  'SNR': { 'format': 'E', 'unit': 'None' },
  #'REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'ERR_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  #'REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  'M500': { 'format': 'E', 'unit': '10^14 h^-1 solar mass' },
  'ERR_M500': { 'format': 'E', 'unit': '10^14 h^-1 solar mass' },
  'Ysz': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'ERR_Ysz': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'THETA': { 'format': 'E', 'unit': 'arcmin' },
  'PAPER': { 'format': '56A', 'unit': 'None' },
  
  # ****** AMI ******
  'INDEX_AMI': { 'format': 'I', 'unit': 'None' },
  'NAME': { 'format': '18A', 'unit': 'None' },
  #'RA': { 'format': 'E', 'unit': 'Degrees' },
  #'DEC': { 'format': 'E', 'unit': 'Degrees' },
  #'GLON': { 'format': 'E', 'unit': 'Degrees' },
  #'GLAT': { 'format': 'E', 'unit': 'Degrees' },
  #'REDSHIFT': { 'format': 'E', 'unit': 'None' },
  #'REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  #'REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  #'ALT_NAME': { 'format': '60A', 'unit': 'None' },
  'COORD_SOURCE': { 'format': '5A', 'unit': 'None' },
  
  # ****** CARMA ******
  'INDEX_CARMA': { 'format': 'I', 'unit': 'None' },
  #'NAME': { 'format': '18A', 'unit': 'None' },
  #'RA': { 'format': 'E', 'unit': 'Degrees' },
  #'DEC': { 'format': 'E', 'unit': 'Degrees' },
  #'GLON': { 'format': 'E', 'unit': 'Degrees' },
  #'GLAT': { 'format': 'E', 'unit': 'Degrees' },
  #'REDSHIFT': { 'format': 'E', 'unit': 'None' },
  #'REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  #'REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  #'COORD_SOURCE': { 'format': '5A', 'unit': 'None' },

  #****** PSZ1 ******
  'INDEX_PSZ1': { 'format': 'I', 'unit': 'None' },
  'NAME': { 'format': '18A', 'unit': 'None' },
  'GLON': { 'format': 'D', 'unit': 'degrees' },
  'GLAT': { 'format': 'D', 'unit': 'degrees' },
  'RA': { 'format': 'D', 'unit': 'degrees' },
  'DEC': { 'format': 'D', 'unit': 'degrees' },
  'RA_MCXC': { 'format': 'E', 'unit': 'degrees' },
  'DEC_MCXC': { 'format': 'E', 'unit': 'degrees' },
  'REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  'REDSHIFT_SOURCE': { 'format': 'I', 'unit': 'None' },
  'REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  'ALT_NAME': { 'format': '66A', 'unit': 'None' },
  'YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'ERRP_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'ERRM_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  'ERRP_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  'ERRM_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  'S_X': { 'format': 'E', 'unit': 'erg/s/cm2' },
  'ERR_S_X': { 'format': 'E', 'unit': 'erg/s/cm2' },
  'Y_PSX_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'SN_PSX': { 'format': 'E', 'unit': 'None' },
  'PIPELINE': { 'format': 'I', 'unit': 'None' },
  'PIPE_DET': { 'format': 'I', 'unit': 'None' },
  'PCCS': { 'format': 'L', 'unit': 'None' },
  'VALIDATION': { 'format': 'I', 'unit': 'None' },
  'ID_EXT': { 'format': '25A', 'unit': 'None' },
  'POS_ERR': { 'format': 'E', 'unit': 'arcmin' },
  'SNR': { 'format': 'E', 'unit': 'None' },
  'COSMO': { 'format': 'L', 'unit': 'None' },
  'COMMENT': { 'format': 'L', 'unit': 'None' },
  'QN': { 'format': 'E', 'unit': 'None' }, 

  # ****** PSZ2 ******
  'INDEX_PSZ2': { 'format': 'I', 'unit': 'None' },
  #'NAME': { 'format': '18A', 'unit': 'None' },
  #'GLON': { 'format': 'D', 'unit': 'degrees' },
  #'GLAT': { 'format': 'D', 'unit': 'degrees' },
  #'RA': { 'format': 'D', 'unit': 'degrees' },
  #'DEC': { 'format': 'D', 'unit': 'degrees' },
  #'POS_ERR': { 'format': 'E', 'unit': 'arcmin' },
  #'SNR': { 'format': 'E', 'unit': 'None' },
  #'PIPELINE': { 'format': 'I', 'unit': 'None' },
  #'PIPE_DET': { 'format': 'I', 'unit': 'None' },
  'PCCS2': { 'format': 'L', 'unit': 'None' },
  'PSZ': { 'format': 'I', 'unit': 'None' },
  'IR_FLAG': { 'format': 'I', 'unit': 'None' },
  'Q_NEURAL': { 'format': 'E', 'unit': 'None' },
  'Y5R500': { 'format': 'E', 'unit': '10^-3 arcmin^2' },
  'Y5R500_ERR': { 'format': 'E', 'unit': '10^-3 arcmin^2' },
  'PSZ2_VALIDATION': { 'format': 'I', 'unit': 'None' },
  'REDSHIFT_ID': { 'format': '25A', 'unit': 'None' },
  #'REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'MSZ': { 'format': 'E', 'unit': '10^14 Msol' },
  'MSZ_ERR_UP': { 'format': 'E', 'unit': '10^14 Msol' },
  'MSZ_ERR_LOW': { 'format': 'E', 'unit': '10^14 Msol' },
  'MCXC': { 'format': '25A', 'unit': 'None' },
  'REDMAPPER': { 'format': '25A', 'unit': 'None' },
  'ACT': { 'format': '25A', 'unit': 'None' },
  'SPT': { 'format': '25A', 'unit': 'None' },
  'WISE_SIGNF': { 'format': 'E', 'unit': 'None' },
  'WISE_FLAG': { 'format': 'I', 'unit': 'None' },
  'AMI_EVIDENCE': { 'format': 'E', 'unit': 'None' },
  #'COSMO': { 'format': 'L', 'unit': 'None' },
  'PSZ2_COMMENT': { 'format': '128A', 'unit': 'None' },

  # ****** PLCK ******
  'INDEX_PLCK': { 'format': 'I', 'unit': 'None' },

  # ****** SPT ******
  'INDEX_SPT': { 'format': 'I', 'unit': 'None' },
  #'CATALOG': { 'format': '7A', 'unit': 'None' },
  #'NAME': { 'format': '16A', 'unit': 'None' },
  #'GLON': { 'format': 'E', 'unit': 'degrees' },
  #'GLAT': { 'format': 'E', 'unit': 'degrees' },
  #'RA': { 'format': 'E', 'unit': 'degrees' },
  #'DEC': { 'format': 'E', 'unit': 'degrees' },
  #'SNR': { 'format': 'E', 'unit': 'None' },
  #'REDSHIFT': { 'format': 'E', 'unit': 'None' },
  #'ERR_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  #'REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  #'M500': { 'format': 'E', 'unit': '10^14 h^-1 solar mass' },
  #'ERR_M500': { 'format': 'E', 'unit': '10^14 h^-1 solar mass' },
  'LX': { 'format': 'E', 'unit': '10^44 erg/s' }
  #'Y': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  #'ERR_Y': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  #'THETA': { 'format': 'E', 'unit': 'arcmin' },
  #'PAPER': { 'format': '59A', 'unit': 'None' },
  
  }


if (len(sys.argv) > 1):
    ascii_file = sys.argv[1] 	# Input ASCII table
    fits_file = sys.argv[2] 	# Output FITS file
else:
    print "\n\t!! Sintax:\t> python create_FITS.py <ascii_file> <fits_file>\n\n"
    exit(0)

#User can define the column delimiter of ASCII table.
delim = raw_input("\n> Please enter the columns delimiter of the ASCII table (default is ','):\t")
if not delim:
  ascii_table=asciidata.open(ascii_file, 'r', delimiter = ',')	# >> ascii_table [COLUMNS] [ROWS] << 
else:
  ascii_table=asciidata.open(ascii_file, 'r', delimiter = delim)	# >> ascii_table [COLUMNS] [ROWS] << 

#Read the fields' names
fields_name = [str(ascii_table[i][0]).strip() for i in range(ascii_table.ncols)]

#Read the 2D array
ascii_data2D = [[ascii_table[j][i] for j in range(len(fields_name))] for i in range(1,ascii_table.nrows)] # Store all in a 2D array, but without the name line

#Define columns' properties

tform = []
tunit = []

for field in fields_name:
  if field not in _FIELDS_DICTIONARY:
    message = "\n\t-> Please enter the format (\'TFORM\') of the new field \"%s\" (e.g.: 5A, E, L, ...): " % (field)
    tform.append(raw_input(message))
    message = "\n\t-> Please enter the unit (\'TUNIT\') of the new field \"%s\" (e.g.: None, arcmin, ...): " % (field)
    tunit.append(raw_input(message))
  else:
    tform.append(_FIELDS_DICTIONARY[field]['format'])
    tunit.append(_FIELDS_DICTIONARY[field]['unit'])
    
#Convert RA and DEC in decimal format

if 'RA' in fields_name:
  index_ra = fields_name.index('RA')
  if (str(ascii_data2D[0][index_ra]).find(":") >= 0): ascii_data2D[index_ra] = [ astCoords.hms2decimal(str(item),':') for item in ascii_data2D[index_ra] ]
if 'DEC' in fields_name:
  index_dec = fields_name.index('DEC')
  if (str(ascii_data2D[0][index_dec]).find(":") >= 0): ascii_data2D[index_dec] = [ astCoords.hms2decimal(str(item),':') for item in ascii_data2D[index_dec] ]
  
#Create/add the columns for the FITS table

for i,field in enumerate(fields_name):
    
    col_tmp = [ascii_data2D[j][i] for j in range(len(ascii_data2D))]
    print field, tform[i], tunit[i], col_tmp
    c_tmp = pyfits.Column(name=str(field), format=tform[i], unit=tunit[i], array=col_tmp)

    if i == 0:
      table_hdu = pyfits.new_table( [c_tmp] )
    else:
      table_hdu.columns.add_col( c_tmp )

hdulist = pyfits.new_table(table_hdu.columns)

##### Change this section to add/remove comments in the FITS Header ####

hdulist.header.add_comment("", before="TTYPE1")
version = 1.0 #raw_input("\n\tPlease enter the number of the current table Version: ")
hdulist.header.add_comment("*** Version" +str(version)+" ***", before="TTYPE1")
today = date.today().strftime("%A %d. %B %Y")
comment = "*** Compiled at IDOC/IAS on %s ***" % (today)
hdulist.header.add_comment(comment, before="TTYPE1")
hdulist.header.add_comment("", before="TTYPE1")
extname = fits_file.split(".")[0]
hdulist.header.update('EXTNAME', extname, before="TTYPE1")

#######################################################################

hdulist.writeto(fits_file)
   
print "\n\t>> Created the file"+bcolors.OKGREEN + " %s " % (fits_file) + bcolors.ENDC+"<<\n" 

