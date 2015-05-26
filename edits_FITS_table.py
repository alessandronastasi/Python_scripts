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
This script updates the content of a fits table, adding new columns
and/or rows (i.e. objects) to it, by considering as input a user-defined ASCII table.                       

The new columns (rows) defined in the ascii file are appended at the end
(bottom) of the fits table.                                             
                                                                           
IMPORTANT: The 1st line of the ASCII table must contain the names   
of the columns, and must be UNCOMMENTED!                            

NOTE: Ra and DEC must be in **decimal degrees**, both in FITS and                                          
ASCII tables.

The syntax is:

$ python edit_FITS.py <table>.fits <ascii_file>

@author: Alessandro NASTASI for IAS - IDOC 
@date: 21/05/2015
'''
__author__ = "Alessandro Nastasi"
__credits__ = ["Alessandro Nastasi"]
__license__ = "GPL"
__version__ = "1.0"
__date__ = "21/05/2015"

import numpy as np
import os, sys, re, time
import string
import asciidata
import pyfits
from datetime import date

#Use the provided astCoords.py file rather than the default module of astLib, 
#since the calcAngSepDeg() of the latter works only for separation <90 deg 
#(tangent plane projection approximation)
import astCoords

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    
#Dictionary containing the FORMAT and UNITS of all (or most of) the fields
_FIELDS_DICTIONARY = { 
  'INDEX': { 'format': 'I', 'unit': 'None' },
  'COORD_SOURCE': { 'format': '5A', 'unit': 'None' },
  'x':{ 'format': 'E', 'unit': 'None' },
  'y':{ 'format': 'E', 'unit': 'None' },
  'z':{ 'format': 'E', 'unit': 'None' },
  
  # ****** ACT ******
  'ACT_INDEX': { 'format': 'I', 'unit': 'None' },
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
  'M500': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'ERR_M500': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'ERR_YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'THETA': { 'format': 'E', 'unit': 'arcmin' },
  #'PAPER': { 'format': '56A', 'unit': 'None' },      # Use PAPER in SPT as bigger format '59A'

  'ACT_CATALOG': { 'format': '7A', 'unit': 'None' },
  'ACT_NAME': { 'format': '18A', 'unit': 'None' },
  'ACT_GLON': { 'format': 'E', 'unit': 'degrees' },
  'ACT_GLAT': { 'format': 'E', 'unit': 'degrees' },
  'ACT_RA': { 'format': 'E', 'unit': 'degrees' },
  'ACT_DEC': { 'format': 'E', 'unit': 'degrees' },
  'ACT_SNR': { 'format': 'E', 'unit': 'None' },
  'ACT_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'ACT_ERR_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'ACT_REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  'ACT_REDSHIFT_REF': { 'format': '19A', 'unit': 'None' },
  'ACT_M500': { 'format': 'E', 'unit': '10^14 h^-1 solar mass' },
  'ACT_ERR_M500': { 'format': 'E', 'unit': '10^14 h^-1 solar mass' },
  'ACT_YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'ACT_ERR_YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'ACT_THETA': { 'format': 'E', 'unit': 'arcmin' },
  'ACT_PAPER': { 'format': '56A', 'unit': 'None' },

  # ****** AMI ******
  'INDEX_AMI': { 'format': 'I', 'unit': 'None' },
  'AMI_INDEX': { 'format': 'I', 'unit': 'None' },
  #'NAME': { 'format': '18A', 'unit': 'None' },
  #'RA': { 'format': 'E', 'unit': 'Degrees' },
  #'DEC': { 'format': 'E', 'unit': 'Degrees' },
  #'GLON': { 'format': 'E', 'unit': 'Degrees' },
  #'GLAT': { 'format': 'E', 'unit': 'Degrees' },
  #'REDSHIFT': { 'format': 'E', 'unit': 'None' },
  #'REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  #'REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  #'ALT_NAME': { 'format': '60A', 'unit': 'None' },
  #'COORD_SOURCE': { 'format': '5A', 'unit': 'None' },

  'AMI_NAME': { 'format': '18A', 'unit': 'None' },
  'AMI_RA': { 'format': 'E', 'unit': 'Degrees' },
  'AMI_DEC': { 'format': 'E', 'unit': 'Degrees' },
  'AMI_GLON': { 'format': 'E', 'unit': 'Degrees' },
  'AMI_GLAT': { 'format': 'E', 'unit': 'Degrees' },
  'AMI_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'AMI_REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  'AMI_REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  'AMI_ALT_NAME': { 'format': '60A', 'unit': 'None' },
  
  # ****** CARMA ******
  'INDEX_CARMA': { 'format': 'I', 'unit': 'None' },
  'CARMA_INDEX': { 'format': 'I', 'unit': 'None' },
  #'NAME': { 'format': '18A', 'unit': 'None' },
  #'RA': { 'format': 'E', 'unit': 'Degrees' },
  #'DEC': { 'format': 'E', 'unit': 'Degrees' },
  #'GLON': { 'format': 'E', 'unit': 'Degrees' },
  #'GLAT': { 'format': 'E', 'unit': 'Degrees' },
  #'REDSHIFT': { 'format': 'E', 'unit': 'None' },
  #'REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  #'REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  #'COORD_SOURCE': { 'format': '5A', 'unit': 'None' },  
  
  'CARMA_NAME': { 'format': '18A', 'unit': 'None' },
  'CARMA_RA': { 'format': 'E', 'unit': 'Degrees' },
  'CARMA_DEC': { 'format': 'E', 'unit': 'Degrees' },
  'CARMA_GLON': { 'format': 'E', 'unit': 'Degrees' },
  'CARMA_GLAT': { 'format': 'E', 'unit': 'Degrees' },
  'CARMA_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'CARMA_REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  'CARMA_REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  'CARMA_M500': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'CARMA_ERR_M500': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },

  #****** PSZ1 ******
  'PSZ1_INDEX': { 'format': 'I', 'unit': 'None' },
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
  #'SNR': { 'format': 'E', 'unit': 'None' },
  'COSMO': { 'format': 'L', 'unit': 'None' },
  'COMMENT': { 'format': 'L', 'unit': 'None' },
  'QN': { 'format': 'E', 'unit': 'None' }, 

  'PSZ1_NAME': { 'format': '18A', 'unit': 'None' },
  'PSZ1_GLON': { 'format': 'D', 'unit': 'degrees' },
  'PSZ1_GLAT': { 'format': 'D', 'unit': 'degrees' },
  'PSZ1_RA': { 'format': 'D', 'unit': 'degrees' },
  'PSZ1_DEC': { 'format': 'D', 'unit': 'degrees' },
  'PSZ1_RA_MCXC': { 'format': 'E', 'unit': 'degrees' },
  'PSZ1_DEC_MCXC': { 'format': 'E', 'unit': 'degrees' },
  'PSZ1_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'PSZ1_REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  'PSZ1_REDSHIFT_SOURCE': { 'format': 'I', 'unit': 'None' },
  'PSZ1_REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  'PSZ1_ALT_NAME': { 'format': '66A', 'unit': 'None' },
  'PSZ1_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'PSZ1_ERRP_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'PSZ1_ERRM_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'PSZ1_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  'PSZ1_ERRP_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  'PSZ1_ERRM_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  'PSZ1_S_X': { 'format': 'E', 'unit': 'erg/s/cm2' },
  'PSZ1_ERR_S_X': { 'format': 'E', 'unit': 'erg/s/cm2' },
  'PSZ1_Y_PSX_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'PSZ1_SN_PSX': { 'format': 'E', 'unit': 'None' },
  'PSZ1_PIPELINE': { 'format': 'I', 'unit': 'None' },
  'PSZ1_PIPE_DET': { 'format': 'I', 'unit': 'None' },
  'PSZ1_PCCS': { 'format': 'L', 'unit': 'None' },
  'PSZ1_VALIDATION': { 'format': 'I', 'unit': 'None' },
  'PSZ1_ID_EXT': { 'format': '25A', 'unit': 'None' },
  'PSZ1_POS_ERR': { 'format': 'E', 'unit': 'arcmin' },
  'PSZ1_SNR': { 'format': 'E', 'unit': 'None' },
  'PSZ1_COSMO': { 'format': 'L', 'unit': 'None' },
  'PSZ1_COMMENT': { 'format': 'L', 'unit': 'None' },
  'PSZ1_QN': { 'format': 'E', 'unit': 'None' }, 

  # ****** PSZ2 ******
  'PSZ2_INDEX': { 'format': 'I', 'unit': 'None' },
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

  'PSZ2_NAME': { 'format': '18A', 'unit': 'None' },
  'PSZ2_GLON': { 'format': 'D', 'unit': 'degrees' },
  'PSZ2_GLAT': { 'format': 'D', 'unit': 'degrees' },
  'PSZ2_RA': { 'format': 'D', 'unit': 'degrees' },
  'PSZ2_DEC': { 'format': 'D', 'unit': 'degrees' },
  'PSZ2_POS_ERR': { 'format': 'E', 'unit': 'arcmin' },
  'PSZ2_SNR': { 'format': 'E', 'unit': 'None' },
  'PSZ2_PIPELINE': { 'format': 'I', 'unit': 'None' },
  'PSZ2_PIPE_DET': { 'format': 'I', 'unit': 'None' },
  'PSZ2_PCCS2': { 'format': 'L', 'unit': 'None' },
  'PSZ2_PSZ': { 'format': 'I', 'unit': 'None' },
  'PSZ2_IR_FLAG': { 'format': 'I', 'unit': 'None' },
  'PSZ2_Q_NEURAL': { 'format': 'E', 'unit': 'None' },
  'PSZ2_Y5R500': { 'format': 'E', 'unit': '10^-3 arcmin^2' },
  'PSZ2_Y5R500_ERR': { 'format': 'E', 'unit': '10^-3 arcmin^2' },
  #'PSZ2_VALIDATION': { 'format': 'I', 'unit': 'None' },
  'PSZ2_REDSHIFT_ID': { 'format': '25A', 'unit': 'None' },
  'PSZ2_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'PSZ2_REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  'PSZ2_MSZ': { 'format': 'E', 'unit': '10^14 Msol' },
  'PSZ2_MSZ_ERR_UP': { 'format': 'E', 'unit': '10^14 Msol' },
  'PSZ2_MSZ_ERR_LOW': { 'format': 'E', 'unit': '10^14 Msol' },
  'PSZ2_MCXC': { 'format': '25A', 'unit': 'None' },
  'PSZ2_REDMAPPER': { 'format': '25A', 'unit': 'None' },
  'PSZ2_ACT': { 'format': '25A', 'unit': 'None' },
  'PSZ2_SPT': { 'format': '25A', 'unit': 'None' },
  'PSZ2_WISE_SIGNF': { 'format': 'E', 'unit': 'None' },
  'PSZ2_WISE_FLAG': { 'format': 'I', 'unit': 'None' },
  'PSZ2_AMI_EVIDENCE': { 'format': 'E', 'unit': 'None' },
  'PSZ2_COSMO': { 'format': 'L', 'unit': 'None' },
  #'PSZ2_COMMENT': { 'format': '128A', 'unit': 'None' },

  # ****** PLCK ******
  'PLCK_INDEX': { 'format': 'I', 'unit': 'None' },
  'INDEX_PLCK': { 'format': 'I', 'unit': 'None' },

  #'NAME': { 'format': '18A', 'unit': 'None' },
  #'GLON': { 'format': 'D', 'unit': 'degrees' },
  #'GLAT': { 'format': 'D', 'unit': 'degrees' },
  #'RA': { 'format': 'D', 'unit': 'degrees' },
  #'DEC': { 'format': 'D', 'unit': 'degrees' },
  #'RA_MCXC': { 'format': 'E', 'unit': 'degrees' },
  #'DEC_MCXC': { 'format': 'E', 'unit': 'degrees' },
  #'REDSHIFT': { 'format': 'E', 'unit': 'None' },
  #'REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  #'REDSHIFT_SOURCE': { 'format': 'I', 'unit': 'None' },
  #'REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  #'ALT_NAME': { 'format': '66A', 'unit': 'None' },
  #'YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  #'ERRP_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  #'ERRM_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  #'M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  #'ERRP_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  #'ERRM_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  #'S_X': { 'format': 'E', 'unit': 'erg/s/cm2' },
  #'ERR_S_X': { 'format': 'E', 'unit': 'erg/s/cm2' },
  #'Y_PSX_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  #'SN_PSX': { 'format': 'E', 'unit': 'None' },
  #'PIPELINE': { 'format': 'I', 'unit': 'None' },
  #'PIPE_DET': { 'format': 'I', 'unit': 'None' },
  #'PCCS': { 'format': 'L', 'unit': 'None' },
  #'VALIDATION': { 'format': 'I', 'unit': 'None' },
  #'ID_EXT': { 'format': '25A', 'unit': 'None' },
  #'POS_ERR': { 'format': 'E', 'unit': 'arcmin' },
  #'SNR': { 'format': 'E', 'unit': 'None' },
  #'COSMO': { 'format': 'L', 'unit': 'None' },
  #'COMMENT': { 'format': 'L', 'unit': 'None' },
  #'QN': { 'format': 'E', 'unit': 'None' }, 

  'PLCK_NAME': { 'format': '18A', 'unit': 'None' },
  'PLCK_GLON': { 'format': 'D', 'unit': 'degrees' },
  'PLCK_GLAT': { 'format': 'D', 'unit': 'degrees' },
  'PLCK_RA': { 'format': 'D', 'unit': 'degrees' },
  'PLCK_DEC': { 'format': 'D', 'unit': 'degrees' },
  'PLCK_RA_MCXC': { 'format': 'E', 'unit': 'degrees' },
  'PLCK_DEC_MCXC': { 'format': 'E', 'unit': 'degrees' },
  'PLCK_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'PLCK_REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  'PLCK_REDSHIFT_SOURCE': { 'format': 'I', 'unit': 'None' },
  'PLCK_REDSHIFT_REF': { 'format': '36A', 'unit': 'None' },
  'PLCK_ALT_NAME': { 'format': '66A', 'unit': 'None' },
  'PLCK_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'PLCK_ERRP_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'PLCK_ERRM_YZ_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'PLCK_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  'PLCK_ERRP_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  'PLCK_ERRM_M_YZ_500': { 'format': 'E', 'unit': '10^14 solar mass' },
  'PLCK_S_X': { 'format': 'E', 'unit': 'erg/s/cm2' },
  'PLCK_ERR_S_X': { 'format': 'E', 'unit': 'erg/s/cm2' },
  'PLCK_Y_PSX_500': { 'format': 'E', 'unit': '10^-4 arcmin squared' },
  'PLCK_SN_PSX': { 'format': 'E', 'unit': 'None' },
  'PLCK_PIPELINE': { 'format': 'I', 'unit': 'None' },
  'PLCK_PIPE_DET': { 'format': 'I', 'unit': 'None' },
  'PLCK_PCCS': { 'format': 'L', 'unit': 'None' },
  'PLCK_VALIDATION': { 'format': 'I', 'unit': 'None' },
  'PLCK_ID_EXT': { 'format': '25A', 'unit': 'None' },
  'PLCK_POS_ERR': { 'format': 'E', 'unit': 'arcmin' },
  'PLCK_SNR': { 'format': 'E', 'unit': 'None' },
  'PLCK_COSMO': { 'format': 'L', 'unit': 'None' },
  'PLCK_COMMENT': { 'format': 'L', 'unit': 'None' },
  'PLCK_QN': { 'format': 'E', 'unit': 'None' }, 

  # ****** SPT ******
  'SPT_INDEX': { 'format': 'I', 'unit': 'None' },
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
  'REDSHIFT_LIMIT': { 'format': 'E', 'unit': 'None' },
  
  'M500_fidCosmo': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'ERR_M500_fidCosmo': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'M500_PlanckCosmo': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'ERR_M500_PlanckCosmo': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'ERR_YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
    
  'LX': { 'format': 'E', 'unit': '10^44 erg/s' },
  'YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'ERR_YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  #'THETA': { 'format': 'E', 'unit': 'arcmin' },
  'PAPER': { 'format': '59A', 'unit': 'None' },
  'XRAY': { 'format': 'L', 'unit': 'None' },
  'STRONG_LENS': { 'format': 'L', 'unit': 'None' },
  
  'SPT_CATALOG': { 'format': '7A', 'unit': 'None' },
  'SPT_NAME': { 'format': '16A', 'unit': 'None' },
  'SPT_GLON': { 'format': 'E', 'unit': 'degrees' },
  'SPT_GLAT': { 'format': 'E', 'unit': 'degrees' },
  'SPT_RA': { 'format': 'E', 'unit': 'degrees' },
  'SPT_DEC': { 'format': 'E', 'unit': 'degrees' },
  'SPT_SNR': { 'format': 'E', 'unit': 'None' },
  'SPT_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'SPT_ERR_REDSHIFT': { 'format': 'E', 'unit': 'None' },
  'SPT_REDSHIFT_TYPE': { 'format': '5A', 'unit': 'None' },
  'SPT_REDSHIFT_REF': { 'format': '19A', 'unit': 'None' },

  'SPT_REDSHIFT_LIMIT': { 'format': 'E', 'unit': 'None' },
  'SPT_XRAY': { 'format': 'L', 'unit': 'None' },
  'SPT_STRONG_LENS': { 'format': 'L', 'unit': 'None' },

  'SPT_M500_fidCosmo': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'SPT_ERR_M500_fidCosmo': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'SPT_M500_PlanckCosmo': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  'SPT_ERR_M500_PlanckCosmo': { 'format': 'E', 'unit': '10^14 h70^-1 solar mass' },
  
  'SPT_LX': { 'format': 'E', 'unit': '10^44 erg/s' },
  'SPT_YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'SPT_ERR_YSZ': { 'format': 'E', 'unit': '10^-6 arcmin squared' },
  'SPT_THETA': { 'format': 'E', 'unit': 'arcmin' },
  'SPT_PAPER': { 'format': '59A', 'unit': 'None' }
  
  }
  
#Name of fields (in FITS/ASCII) sometimes called individually in the script

#For Mass and Err_Mass, more than one label could be defined just as elements of the arrays
name_mass_key = ['M500']
name_errMass_key = ['ERR_M500']

name_ra_key = 'RA'
name_dec_key = 'DEC'
name_coordinates_keys =  ['RA_MCXC', 'DEC_MCXC', name_ra_key, name_dec_key]

name_Name_key = 'NAME'  
name_index_key = 'INDEX'
name_catalog_key = 'CATALOG'
name_redshift_key = 'REDSHIFT'
name_zLimit_key = 'REDSHIFT_LIMIT'
name_zErr_key = 'ERR_REDSHIFT'
name_zType_key = 'REDSHIFT_TYPE'
name_zRef_key = 'REDSHIFT_REF'
name_altName_key = 'ALT_NAME'
name_paper_key = 'PAPER'

#Undef values for some kind of fields
_UNDEF_VALUES_ = {
  'FLOAT' : {np.nan},
  'INT' : {-1},
  'STRING' : {'NULL'},
  name_zType_key : {'undef'},
  'PIPELINE' : {0},
  'PIPE_DET' : {0}
  }

def remove_duplicated_names(string):
  '''
  This function removes duplicated names of a string, assuming they are separated by ';'
  In addition, it takes out 'NULL', 'NaN', 'False' from the final, composite string.
  It is used for the creation of ALT_NAME field.
  '''
  string = string.replace('; ',';')
  tmp = [item for item in string.split(';') if item.upper() not in ["-", "NULL", "NAN", "NONE", "FALSE"] and len(item)>0 ]
  # *** This lines of code help preserving the order ot the names ***
  tmp_uniq = []
  set_tmp = set()
  for item in tmp:
    if item not in set_tmp:
      tmp_uniq.append(item)
      set_tmp.add(item)
  # ******************************************************************
  
  if len(tmp)==0: new_string = '-'
  else: new_string =  "; ".join(tmp_uniq)
  return new_string
 
def set_undef_values(fits_data):
  '''
  Set the proper 'undef' values according to the format/name of the field
  '''
  print "\n\t>> Checking/setting undefined values for the different fields ..."
  for i, name in enumerate(fits_data.names):
    sys.stdout.write('\t%i/%i > %s (format %s) : Done                                        \r' % (i+1, len(fits_data.names), name, fits_data.formats[i]))
    sys.stdout.flush()
    for j in range(fits_data.size):
      if name == name_index_key:
	if fits_data[name_Name_key][j] <= 0: fits_data[j][i] = -1
      elif name == name_redshift_key and fits_data[name][j] == -1.0:
	fits_data[j][i] = np.nan
      elif name.find(name_zType_key) >= 0 and str(fits_data[name][j]) == 'Null':
	fits_data[j][i] = "undef"
      elif fits_data.formats[i] in 'EDJ':
	if str(fits_data[j][i]) in ['-1.6375e+30','-1.63750e+30', '-1.6375E+30', '-1.63750E+30', 'None', 'NULL']:
	  fits_data[j][i] = np.nan
      elif fits_data.formats[i].find('A') >= 0:
	fits_data[j][i] = remove_duplicated_names(fits_data[j][i])
	if str(fits_data[j][i]).upper() in ["", "0.0", "NULL", "NAN", "NONE", "FALSE"]  or str(fits_data[j][i]) == 'False':
	  fits_data[j][i] = "-"
      elif name in ['PIPELINE','PIPE_DET']:
	if fits_data[j][i] <= 0: fits_data[j][i] = 0
  print '\n'
  return fits_data

def recreate_reformatted_column(hdulist, field_name, new_format, new_vector):
  '''
  Update the length (format) of a 'STRING' (format = 'xA') FIELD. 
  The only way, though, is to re-create the column with the new format.
  It is used during the creation of NAME, ALT_NAME or REDSHIFT_REF.
  '''
  name_vec = []
  format_vec = []
  unit_vec = []
  
  fits_keywds = hdulist.data.names
  coldefs = pyfits.ColDefs(hdulist.columns)
  
  #Store attributes of the kewyords after FIELD
  for j in range(fits_keywds.index(field_name)+1, len(fits_keywds)):
    name_vec.append(coldefs.names[j])
    format_vec.append(coldefs.formats[j])
    unit_vec.append(coldefs.units[j])
  
  #Delete the kewyords after FIELD
  tmp = 0
  for j in range(fits_keywds.index(field_name)+1, len(fits_keywds)):
    coldefs.del_col(name_vec[tmp])
    tmp+=1
    
  #Delete FIELD
  coldefs.del_col(field_name)

  #Re-create FIELD with the new format
  col_tmp = pyfits.Column(name = field_name, format = new_format, unit = 'None', array = new_vector)
  coldefs.add_col(col_tmp)
  hdulist.columns = coldefs
  
  #Re-create all the kewyords after FIELD, with their attributes
  tmp = 0
  data_vec_tmp = []
  for j in range(fits_keywds.index(field_name)+1, len(fits_keywds)):
    data_vec_tmp = hdulist.data[name_vec[tmp]]
    col_tmp = pyfits.Column(name = name_vec[tmp], format = format_vec[tmp], unit = unit_vec[tmp], array = data_vec_tmp)
    coldefs.add_col(col_tmp)
    tmp +=1
    data_vec_tmp = []
    
  hdulist = pyfits.new_table(coldefs)
  return hdulist

'''
  *** >> START << ***
'''

if (len(sys.argv) > 1):
    fits_file = sys.argv[1] 
    ascii_file = sys.argv[2] 
else:
    print bcolors.WARNING +  "\n\tSintax:\t$ python edit_FITS.py <fits_file> <ascii_file>\n" + bcolors.ENDC
    os._exit(0)

#Open the output file
file_report_name = 'summary_updates.tab'
file_report = open(file_report_name, 'w')

question = bcolors.OKBLUE+ "[Q]" + bcolors.ENDC
info = bcolors.WARNING+ "[I]" + bcolors.ENDC
error = bcolors.FAIL+ "[ERR]" + bcolors.ENDC

#User can define the columns delimiter in the ASCII table.
delim=raw_input("\n%s Please enter the column delimiter of the ASCII table (default is ','):\t" % question)
if not delim:
# Read the ascii table, with the structure: ascii_table[COLUMNS][ROWS]
  ascii_table=asciidata.open(ascii_file, 'r', delimiter=',')
else:
  ascii_table=asciidata.open(ascii_file, 'r', delimiter=delim)
  
Ncol_ascii = ascii_table.ncols
Nrows_ascii = (ascii_table.nrows) - 1 #1st excluded because of the header

print "\n\t\t **** ASCII table details ****"
print "\t\t Number of columns: %s" % (Ncol_ascii)
print "\t\t Number of rows: %s" % (Nrows_ascii)
print "\t\t **** **** **** **** **** ****"

ascii_keywds=[]
keys_form_unit = {}

for i in range(ascii_table.ncols):
  tmpKey = str(ascii_table[i][0]).strip()
  ascii_keywds.append(tmpKey)
  if tmpKey in _FIELDS_DICTIONARY:
    keys_form_unit[tmpKey] = {}
    keys_form_unit[tmpKey]['TFORM'] = _FIELDS_DICTIONARY[tmpKey]['format']
    keys_form_unit[tmpKey]['TUNIT'] = _FIELDS_DICTIONARY[tmpKey]['unit']

#Read the fits table
hdulist = pyfits.open(fits_file)
fits_header = hdulist[1].header	# HEADER 
fits_data = hdulist[1].data 		# DATA 

#Number of columns in FITS table
Ncol_fits = int(fits_header['TFIELDS'])

#Number of rows in FITS table
Nrows_fits = fits_header['NAXIS2']

print "\n\t\t **** FITS table details ****"
print "\t\t Number of columns: %s" % (Ncol_fits)
print "\t\t Number of rows: %s" % (Nrows_fits)
print "\t\t **** *** *** *** *** *** ***"

#Fits keywords read from the header
fits_keywds=[]
original_fits_keywds = []

for i in range(Ncol_fits):
  original_fits_keywds.append(fits_data.names[i])
  fits_keywds.append(fits_data.names[i])

#Find the keywords written in the ASCII file and the corresponding columns in the FITS table...
common_keywds=[]
commonKeywds_index=[]
keywds_to_update=[]
for j in range(Ncol_fits):
  if fits_keywds[j] in ascii_keywds:
    common_keywds.append(fits_keywds[j])
    commonKeywds_index.append(j+1)

    #Only the fields with new values will be updated. Also NAME, RA and DEC are allowed to change
    keywds_to_update.append(fits_keywds[j])

print "\n\t%s The following keyword(s) will be updated in the FITS table: " % info , keywds_to_update

#...also selecting the NEW keywords defined in the ASCII file...
keywds_to_add=[item for item in ascii_keywds if item not in fits_keywds]

print "\n\t%s The following new keyword(s) will be added to the FITS table: " % info , keywds_to_add

#To associate TFORM and TUNIT to each field, first look into _FIELDS_DICTIONARY
#If nothing is found ther, ask the user to enter them manually
for i in range(len(keywds_to_add)):
  if keywds_to_add[i] not in _FIELDS_DICTIONARY:
    keys_form_unit[keywds_to_add[i]] = {}
    message = "\n%s Please enter the format (\'TFORM\') of the new field \"%s\" (e.g.: 5A, E, L, ...): " % (question, keywds_to_add[i])
    keys_form_unit[keywds_to_add[i]]['TFORM'] = raw_input(message)
    message = "\n%s Please enter the unit (\'TUNIT\') of the new field \"%s\" (e.g.: None, arcmin, ...): " % (question, keywds_to_add[i])
    keys_form_unit[keywds_to_add[i]]['TUNIT'] = raw_input(message)
  else:
    keys_form_unit[keywds_to_add[i]] = {}
    keys_form_unit[keywds_to_add[i]]['TFORM'] = _FIELDS_DICTIONARY[keywds_to_add[i]]['format']
    keys_form_unit[keywds_to_add[i]]['TUNIT'] = _FIELDS_DICTIONARY[keywds_to_add[i]]['unit']
        
  # ...to be appended into the 'fits_keywds' array
  fits_keywds.append(keywds_to_add[i])

'''
  *** Add the NEW COLUMNS to FITS table ***
'''

#Initialize new columns
a_tmp = []

coldefs = pyfits.ColDefs(hdulist[1].columns)
columns = []

for keys in keywds_to_add:
  if keys_form_unit[keys]['TFORM'] == 'E' or keys_form_unit[keys]['TFORM'] == 'D':
    a_tmp = [-1.6375E+30] * Nrows_fits # Initialize Float with empty array
  elif keys_form_unit[keys]['TFORM'] == 'I':
    a_tmp = [-1] * Nrows_fits # Initialize Integer with -1 array
  elif keys_form_unit[keys]['TFORM'] == 'L':
    a_tmp = [False] * Nrows_fits # Initialize logical with True array
  elif keys_form_unit[keys]['TFORM'].find('A') >= 0:
    a_tmp = ['Null'] * Nrows_fits

  while True:
    #Check between field format and values.
    try:
      col_tmp = pyfits.Column(name=keys, format=keys_form_unit[keys]['TFORM'], unit=keys_form_unit[keys]['TUNIT'], array=a_tmp)
      columns.append(col_tmp)
      break
    except ValueError:
      print bcolors.FAIL+ "\n\t\t*** FORMAT INCONSISTENT WITH DATA ***" + bcolors.ENDC
      keys_form_unit[keys]['TFORM'] = raw_input("\n%s Please, enter again the format (\'TFORM\') of the new field \"%s\": " % (question, keys))
         
'''
  *** 1st data UPDATE: new fields added as new columns ***
'''

#New for Pyfits > 2.3
for i in columns: coldefs.add_col(i)
hdulist = pyfits.new_table(coldefs)

#Old Python version
#hdulist = pyfits.BinTableHDU.from_columns(coldefs)

fits_data = hdulist.data

'''
  *** Object identification via POSITION matching, NAME or INDEX  ***
'''
match_option = False
match_radius = 300.0 # default = 5 arcmin

name_index_fits = ''
name_index_ascii = ''

print '\n%s Which method do you want to use for the object matching: by POSITION (1) by NAME (2) or by INDEX (3)?' % question
while match_option == False:
  message = "\n\t-> Please enter 1, 2 or 3:   "
  method = raw_input(message)
  if method == '1': 
    #Check if RA & DEC are actually in FITS and ASCII tables
    if name_ra_key not in fits_data.names or name_dec_key not in fits_data.names or name_ra_key not in ascii_keywds or name_dec_key not in ascii_keywds:
      print bcolors.FAIL+ "\n\t>> NO %s and %s found in FITS and ASCII tables: POSITION matching not possible <<" % (name_ra_key, name_dec_key) + bcolors.ENDC
    else:
      match_option = method
      match_radius = float(raw_input('\n\t%s Please enter the match radius (in arcsec): ' % question))
  elif method == '2' : match_option = method
  elif method == '3' :
    check_name_index_fits = False
    while check_name_index_fits == False:
      name_index_fits = raw_input('\n\t-> Please enter the column name of the INDEX in the FITS file: ')
      if name_index_fits not in fits_keywds:
	print bcolors.FAIL+ "\n\t*** '%s' NOT in FITS Keywords ***" % name_index_fits+ bcolors.ENDC
      else:
	check_name_index_fits = True
	index_fits = np.array( fits_data[name_index_fits] )

    check_name_index_ascii = False
    while check_name_index_ascii == False:
      name_index_ascii = raw_input('\n\t-> Please enter the column name of the INDEX in the ASCII file: ')
      if name_index_ascii not in ascii_keywds:
	print bcolors.FAIL+ "\n\t*** '%s' NOT in ASCII Keywords ***" % name_index_ascii+ bcolors.ENDC
      else:
	check_name_index_ascii = True
	index_ascii = [ (ascii_table[k][j]) for k in range(ascii_table.ncols) if ascii_table[k][0] == name_index_ascii for j in range(1,ascii_table.nrows) ]
      
    match_option = method

  else: print bcolors.FAIL+ "\n\t*** Wrong option ***"+ bcolors.ENDC

name_fits = np.array(fits_data[name_Name_key])
ra_fits = np.array(fits_data[ name_ra_key ])
dec_fits = np.array(fits_data[ name_dec_key ])

name_ascii = []
ra_ascii = []
dec_ascii = []

for k in range(ascii_table.ncols):
  if ascii_keywds[k]==name_Name_key:
    for j in range(ascii_table.nrows -1): name_ascii.append((ascii_table[k][j+1]).strip())
  if ascii_keywds[k]==name_ra_key:
    for j in range(ascii_table.nrows -1): ra_ascii.append(float(ascii_table[k][j+1]))
  elif ascii_keywds[k]==name_dec_key:
    for j in range(ascii_table.nrows -1): dec_ascii.append(float(ascii_table[k][j+1]))

dist_asec = []

#Two arrays with the indexes of the matching objects
rowAscii_match = []	# ASCII rows
rowFits_match = []	# FITS rows

#Array with the indexes of the NEW objects found in the ASCII file (if any)
rowAscii_new = []

method_dict = {
  '1' : 'POSITION (dist < %.1f")' % match_radius,
  '2' : 'NAME',
  '3' : 'INDEX'
  }

print "\n\t>> Matching ASCII/FITS tables by %s ...\n" % method_dict[method]

num_tot_matches = 0
for j in range(Nrows_fits):
  num_multiple_matches = 0
  id_matches = []
  ra_dec_matches = []
  
  if match_option == '1':
    tmp_idxs_matches = []
    tmp_dist_matches = []
    
    for i in range(Nrows_ascii):
      dist_tmp = 3600. * astCoords.calcAngSepDeg(float(ra_fits[j]), float(dec_fits[j]), ra_ascii[i], dec_ascii[i])
      if dist_tmp <= match_radius:
	tmp_idxs_matches.append(i)
	tmp_dist_matches.append(round(dist_tmp,1))
	num_tot_matches += 1
	num_multiple_matches += 1
	
    idx_match = 0
    if len( tmp_idxs_matches ) > 1:
      print bcolors.WARNING+ "\n\t! WARNING ! %i objects found within %.1f arcsec from %s \n" % ( len(tmp_idxs_matches), match_radius, name_fits[j]) + bcolors.ENDC
      for idx in range( len(tmp_idxs_matches) ): print '\t%i: %s (dist = %s")' % ( (idx+1, name_ascii[ tmp_idxs_matches[idx]], tmp_dist_matches[idx] ) )
      tmp_check = False
      while tmp_check == False:
	tmp_entry = int(raw_input('\t-> Please enter the number of the matching object: '))
	if tmp_entry in range(1, len(tmp_idxs_matches)+1 ): 
	  tmp_check = True
	  idx_match = tmp_idxs_matches[ tmp_entry - 1 ]
	else:
	  print bcolors.FAIL+ "\n\t*** Wrong option ***\n"+ bcolors.ENDC
	
      id_matches.append((name_ascii[idx_match]).strip())
      ra_dec_matches.append(ra_ascii[idx_match])
      ra_dec_matches.append(dec_ascii[idx_match])
      
      # NOTE: When the ascii_table is called, the corresponding index is (rowAscii_match + 1) because of the additional line for the HEADER
      rowAscii_match.append(idx_match)
      rowFits_match.append(j)

    elif len( tmp_idxs_matches ) == 1:
      idx_match = tmp_idxs_matches[0]
      
      id_matches.append((name_ascii[idx_match]).strip())
      ra_dec_matches.append(ra_ascii[idx_match])
      ra_dec_matches.append(dec_ascii[idx_match])
      
      # NOTE: When the ascii_table is called, the corresponding index is (rowAscii_match + 1) because of the additional line for the HEADER
      rowAscii_match.append(idx_match)
      rowFits_match.append(j)
      
  elif match_option == '2':
    for i in range(Nrows_ascii):
      if (name_fits[j]).strip() == (name_ascii[i]).strip():
	num_multiple_matches += 1
	num_tot_matches += 1
	if num_multiple_matches > 1: 
	
	  print '%s Found %i objects with the same name : %s\nAborted.\n' % (error, num_multiple_matches, name_fits[j]); os._exit(0)
	  
	# NOTE: When the ascii_table is called, the corresponding index is (rowAscii_match + 1) because of the additional line for the HEADER  
	rowAscii_match.append(i)
	rowFits_match.append(j)

  elif match_option == '3':
    for i in range(Nrows_ascii):
      if int(index_fits[j]) == int(index_ascii[i]) and (int(index_fits[j]) >= 0 and int(index_ascii[i]) >= 0):
	num_tot_matches += 1

	# NOTE: When the ascii_table is called, the corresponding index is (rowAscii_match + 1) because of the additional line for the HEADER
	rowAscii_match.append(i)
	rowFits_match.append(j)
	break

for i in range(Nrows_ascii):
  if i not in rowAscii_match: rowAscii_new.append(i) # Rows numbers of the NEW clusters, in the ASCII file

print "\n\t%s Found %s matching clusters between FITS/ASCII table to be UPDATED in the FITS table" % (info, len(rowAscii_match))

print "\n\t%s Found %s NEW clusters in the ASCII table to be ADDED to the FITS table" % (info, len(rowAscii_new))

#Store the names of the common/new clusters
idx_name = fits_keywds.index(name_Name_key)
clName_fits=[]

for k in range(Nrows_fits):
  clName_fits.append(fits_data[k][idx_name])

common_clNames=[]
new_clNames=[]

for i, idx in enumerate(rowAscii_match):
  common_clNames.append(clName_fits[rowFits_match[i]])
  
for idx in rowAscii_new:
  idx_name = ascii_keywds.index(name_Name_key)
  new_clNames.append( ascii_table[idx_name][idx+1] )

#Define the MASS conversion factor, only if it is found in ASCII table:
h_factor = 1.0
tmp_check = False

mass_in_ascii = set(name_mass_key) & set(ascii_keywds)
if mass_in_ascii:
  print "\n%s Concerning %s, do you want to:\n\t1) Convert from h70^-1 -> h100^-1\n\t2) Convert from h100^-1 -> h70^-1\n\t3) Keep the original values of the ASCII table" % (question, mass_in_ascii.pop())
  while tmp_check == False:
    message = "\n\t-> Please enter 1, 2 or 3:   "
    h_opt = raw_input(message)
    if h_opt == '1': h_factor = 0.7; tmp_check = True
    elif h_opt == '2': h_factor = 1./0.7; tmp_check = True
    elif h_opt == '3': h_factor = 1.; tmp_check = True
    else: print bcolors.FAIL+ "\n\t*** Wrong option ***"+ bcolors.ENDC

newRow_num = Nrows_fits + len(rowAscii_new)

'''
  *** 2nd data UPDATE: add the new clusters as new (initially empty) rows ***
'''
hdulist = pyfits.new_table(hdulist, nrows=newRow_num)

#Add 'CATALOG' to the new clusters (if any)
if name_catalog_key in fits_keywds and name_catalog_key not in ascii_keywds and len(rowAscii_new) > 0:
  new_catalog = raw_input("\n%s Please enter the value of %s for the new cluster(s): " % (question, name_catalog_key))

  
'''
  *** Update the PAPER column ***
'''
paper_flag = False
updated_paper_vec = []
max_length_paper = 0
cnt = 0

#If 'PAPER' is defined in the ASCII table, but it is not in the FITS and there are NO NEW objects, the latter is updated with the former
if name_paper_key in ascii_keywds and name_paper_key not in fits_keywds and len(rowAscii_new) == 0:
  for j in range(Nrows_fits):
    
    #Update only those clusters specified in the ASCII table
    if j in rowFits_match:
      paper_tmp = ascii_table[ascii_keywds.index(name_paper_key)][rowAscii_match[cnt]+1]
      cnt += 1
    else:
      paper_tmp = "Null"
    
    paper_tmp = remove_duplicated_names(paper_tmp)
    updated_paper_vec.append(paper_tmp)
    if len(paper_tmp) > max_length_paper: max_length_paper = len(paper_tmp)
 
#If 'PAPER' is defined in the FITS table, it is updated for the common clusters (and created for the new clusters) with the one defined in the ASCII table.
#If no 'PAPER' is found in ASCII, user is asked to enter it manually.
elif name_paper_key in fits_keywds:
  new_paper_vec = []
  col_paper_fits = fits_keywds.index(name_paper_key)

  if name_paper_key in ascii_keywds:
    paper_flag = True
    for i in range(Nrows_ascii):
      new_paper_vec.append( ascii_table[ascii_keywds.index(name_paper_key)][i+1].strip() )
  else:
    #The new reference is asked to be added manually only if new clusters are found
    if len(new_clNames)>0:
      tmp_new_paper = raw_input("\n%s Please insert the new reference to add: " % question)
      new_paper_vec=[tmp_new_paper for x in range( Nrows_ascii ) ]
      paper_flag = True
    else:
      new_paper_vec=['' for x in range( Nrows_ascii ) ]
      
  #Update those clusters in common with ASCII and FITS table
  for j in range(Nrows_fits):
    paper_old = (fits_data[j][col_paper_fits]).strip()
    if j in rowFits_match:
      if paper_old == "Null":
	paper_tmp = new_paper_vec[ rowAscii_match[cnt] ]	#Here the '+1' correction is not necessary because also new_paper_vec[] contains the header line
	cnt+=1
      else:
	paper_tmp = paper_old+"; "+new_paper_vec[ rowAscii_match[cnt] ]	#Here the '+1' correction is not necessary because also new_paper_vec[] contains the header line
	cnt += 1
    else:
      paper_tmp = paper_old
  
    paper_tmp = remove_duplicated_names(paper_tmp)
    updated_paper_vec.append(paper_tmp)
    if len(paper_tmp) > max_length_paper: max_length_paper = len(paper_tmp)
  
#Delete the old 'PAPER' column and update it with a new one defined according to the above case.
if name_paper_key in fits_keywds and paper_flag: 
  hdulist.columns.del_col(name_paper_key)
  
  #Add the new PAPER field, as last column
  col_tmp = pyfits.Column(name=name_paper_key, format=str(max_length_paper)+'A', unit = 'None', array=updated_paper_vec)
  paper_flag = True

if paper_flag:
  coldefs = pyfits.ColDefs(hdulist.columns)
  coldefs.add_col(col_tmp)
  hdulist = pyfits.new_table(coldefs)


#Update PAPER for common cluster
len_ALT_NAME = []
new_altName_vec = []
old_altName_vec = []
new_altName = ""
cnt = 0

altName_flag = False
name_in_altName = False
replace_altName = False

#Handle the NAME/ALT_NAME update in case of position/index matching:
if len(common_clNames) > 0:
    
  if name_altName_key not in ascii_keywds and name_altName_key in fits_keywds:
    if name_Name_key in fits_keywds and name_Name_key in ascii_keywds:
      answer_check = False
      tmp = raw_input("\n\t%s Do you want to add the old clusters' %s listed in FITS table to %s? [y/n]: " % (question, name_Name_key, name_altName_key) )
      while answer_check == False:
	if tmp in 'yesYES1' and tmp != '': 
	  name_in_altName = True
	  answer_check = True
	elif tmp in 'nN' and tmp != '': answer_check = True
	else: tmp = raw_input(bcolors.FAIL+ "\n\t\t*** Please enter a valid answer ***" + bcolors.ENDC + ' [y/n] : ')
    
    col_altName_fits = fits_keywds.index( name_altName_key )

    for j in range(Nrows_fits):

      oldVal_fits = (fits_data[j][col_altName_fits]).strip()
      old_altName_vec.append(oldVal_fits)
      if j in rowFits_match:
	
	#Adds the NAME to "ALT_NAME", if it does not exist already
	if name_in_altName:
	  altName_flag = True

	  name_fits = np.array(fits_data[name_Name_key]) 
	  new_altName = oldVal_fits+"; "+name_fits[j]
	
	else: new_altName = oldVal_fits
	
	new_altName = remove_duplicated_names(new_altName)
	new_altName_vec.append(new_altName)
	len_ALT_NAME.append(len(new_altName))

	cnt += 1
	  
      else:
	new_altName = remove_duplicated_names(oldVal_fits)
	new_altName_vec.append(oldVal_fits)

  elif name_altName_key in ascii_keywds and name_altName_key in fits_keywds:
    
    answer_check = False
    tmp = raw_input("\n\t%s %s is both in ASCII/FITS tables. Do you want the ASCII values to REPLACE or to be APPENDED to the FITS ones? [r/a]: " % (question, name_altName_key) )
    while answer_check == False:
      if tmp in 'rR' and tmp != '': 
	replace_altName = True
	answer_check = True
      elif tmp in 'aA' and tmp != '': answer_check = True
      else: tmp = raw_input(bcolors.FAIL+ "\n\t\t*** Please enter a valid answer ***" + bcolors.ENDC + ' [r/a] : ')
	
    if name_Name_key in fits_keywds and name_Name_key in ascii_keywds:
      answer_check = False
      tmp = raw_input("\n\t%s Do you want to add the old clusters' %s listed in FITS table to %s? [y/n]: " % (question, name_Name_key, name_altName_key) )
      while answer_check == False:
	if tmp in 'yesYES1' and tmp != '': 
	  name_in_altName = True
	  answer_check = True
	elif tmp in 'nN' and tmp != '': answer_check = True
	else: tmp = raw_input(bcolors.FAIL+ "\n\t\t*** Please enter a valid answer ***" + bcolors.ENDC + ' [y/n] : ')
   
    col_altName_ascii = ascii_keywds.index( name_altName_key )
    
    if replace_altName:
      altName_flag = True
      print "\n\t%s %s replaced" % (info, name_altName_key)

      if name_in_altName:
	names_fits = fits_data[name_Name_key].strip()
	for j in range(Nrows_fits):
	  oldVal_fits = (fits_data[ name_altName_key ][j]).strip()
	  old_altName_vec.append(oldVal_fits)
	  if j in rowFits_match:
	    new_altName = ascii_table[col_altName_ascii][rowAscii_match[cnt]+1]+"; "+name_fits[j]
	    cnt+=1  
	  else: new_altName = oldVal_fits
	  
	  new_altName = remove_duplicated_names(new_altName)
	  new_altName_vec.append(new_altName)
      else:
	for j in range(Nrows_fits):
	  oldVal_fits = (fits_data[ name_altName_key ][j]).strip()
	  old_altName_vec.append(oldVal_fits)
	  if j in rowFits_match: 
	    new_altName = ascii_table[col_altName_ascii][rowAscii_match[cnt]+1]
	    cnt+=1  
	  else: new_altName = oldVal_fits
	  
	  new_altName = remove_duplicated_names(new_altName)
	  new_altName_vec.append(new_altName)
	  
    elif not replace_altName:
      if name_in_altName:
	altName_flag = True
	print '\n\t%s %s appended & %s added' % (info, name_altName_key, name_Name_key)
	names_fits = fits_data[name_Name_key].strip()
	for j in range(Nrows_fits):
	  oldVal_fits = (fits_data[ name_altName_key ][j]).strip()
	  old_altName_vec.append(oldVal_fits)
	  if j in rowFits_match:
	    new_altName = "; ".join([ oldVal_fits, ascii_table[col_altName_ascii][rowAscii_match[cnt]+1], name_fits[j] ])
	    cnt+=1  
	  else:
	    new_altName = oldVal_fits
	  
	  new_altName = remove_duplicated_names(new_altName)
	  new_altName_vec.append(new_altName)
      else:
	for j in range(Nrows_fits):
	  oldVal_fits = (fits_data[ name_altName_key ][j]).strip()
	  old_altName_vec.append(oldVal_fits)
	  if j in rowFits_match: 
	    if oldVal_fits in [np.nan, "NULL", "NaN", "False"]: new_altName = ascii_table[col_altName_ascii][rowAscii_match[cnt]+1]
	    else: 
	      new_altName = "%s; %s" % (oldVal_fits, ascii_table[col_altName_ascii][rowAscii_match[cnt]+1])
	    cnt+=1  
	  else: new_altName = oldVal_fits
	  
	  new_altName = remove_duplicated_names(new_altName)
	  new_altName_vec.append(new_altName)
	    
    #Compute the max length of ALT_NAME in fits and ascii
    maxLength_altName_fits = max([len(item) for item in fits_data[ name_altName_key ]])
    maxLength_altName_ascii = max([len(item) for item in ascii_table[col_altName_ascii]])
    
    maxLength_altName_new = max([len(item) for item in new_altName_vec])
    
    len_ALT_NAME = [maxLength_altName_fits, maxLength_altName_ascii, maxLength_altName_new]

'''
  *** Update the length of ALT_NAME. The only way, though, is to re-create the column with the new format ***
'''
if altName_flag:
  
  #Delete the old 'ALT_NAME' column
  name_vec = []
  format_vec = []
  unit_vec = []
  
  #Store attributes of the kewyords after ALT_NAME
  for j in range(fits_keywds.index(name_altName_key)+1, len(fits_keywds)):
    name_vec.append(coldefs.names[j])
    format_vec.append(coldefs.formats[j])
    unit_vec.append(coldefs.units[j])
  
  #Delete the kewyords after ALT_NAME
  tmp = 0
  for j in range(fits_keywds.index(name_altName_key)+1, len(fits_keywds)):
    coldefs.del_col(name_vec[tmp])
    tmp+=1
    
  #Delete ALT_NAME
  coldefs.del_col(name_altName_key)

  #Re-create ALT_NAME with the new format
  col_tmp = pyfits.Column(name=name_altName_key, format=str(max(len_ALT_NAME))+'A', unit = 'None', array=new_altName_vec)
  coldefs.add_col(col_tmp)
  hdulist.columns = coldefs
  
  #Re-create all the kewyords after ALT_NAME, with their attributes
  tmp = 0
  data_vec_tmp = []
  
  for j in range(fits_keywds.index(name_altName_key)+1, len(fits_keywds)):
    data_vec_tmp = hdulist.data[name_vec[tmp]]
    col_tmp = pyfits.Column(name=name_vec[tmp], format=format_vec[tmp], unit = unit_vec[tmp], array=data_vec_tmp)
    coldefs.add_col(col_tmp)
    tmp +=1
    data_vec_tmp = []
    
  hdulist = pyfits.new_table(coldefs)

'''
  *** Write summary report for matching/new clusters ***
  
and also
    
  *** 3rd data UPDATE: the columns of new clusters are filled in with the correct values ***
'''

#Write summary for common clusters (if any)
if len(rowAscii_match) > 0:
  length_new_field = []
  index_ascii_field_vec = []
    
  tmp_lenght = ''
  for fields in ascii_keywds:
    index_ascii_field = ascii_keywds.index(fields)
    index_ascii_field_vec.append(index_ascii_field)
    index_fits_field = coldefs.names.index(fields)
    if coldefs.formats[index_fits_field].find('A') >= 0:
      tmp_lenght = coldefs.formats[index_fits_field].split('A')[0]
    elif coldefs.formats[index_fits_field].find('E') >= 0 or coldefs.formats[index_fits_field].find('D') >= 0:
      tmp_lenght = '15' #For float and double, string size fixed to 15
    elif coldefs.formats[index_fits_field].find('I') >= 0:
      max_len_int =  max(len(str(elem).strip()) for elem in ascii_table[index_ascii_field])
      tmp_lenght = str(max_len_int + 3)
    elif coldefs.formats[index_fits_field].find('L') >= 0:
      tmp_lenght = '6'
    
    length_new_field.append( max( int(tmp_lenght), len(fields)+3 ) )
      
  file_report.write("\n# >>>> CLUSTERS PROPERTIES ** UPDATED ** IN THE FITS TABLE <<<<\n\n")
  to_write = ""

  #Write/format the header of each column
  for tmp, fields in enumerate(ascii_keywds):
    
    max_len_new = length_new_field[tmp]
    
    if fields in fits_keywds:
      max_len_old = max(len(str(elem).strip()) for elem in fits_data[fields])
    else:
      max_len_old = max_len_new

    if fields in [name_Name_key, name_zRef_key]:
      
      #Update the length of NAME or REDSHIFT_REF (increase its TFORM) if necessary
      #by comparing the max length of its values in old (fits) and new (ascii) file
      maxLength_fits = max([len(item) for item in fits_data[fields]])
      maxLength_ascii = max([len(item) for item in ascii_table[index_ascii_field_vec[tmp]] ])
      
      #If ascii names are longer than in fits, NAME is deleted and re-created with a bigger format, but keeping (for the moment) the old values
      if maxLength_ascii > maxLength_fits:
	print '\n\t%s New %ss are longer than ones in fits: recreating the column with larger size (%sA -> %sA)' % (info, fields, maxLength_fits, maxLength_ascii)
	
	new_format = '%sA' % maxLength_ascii

	hdulist = recreate_reformatted_column(hdulist, fields, new_format, hdulist.data[fields] ) #ascii_table[index_ascii_field_vec[tmp]])

    #Define lengths for ALT_NAME
    elif fields == name_altName_key and altName_flag:
      max_len_old = max([len(item) for item in old_altName_vec])
      max_len_new = max([len(item) for item in new_altName_vec])
      
    #Define lengths for PAPER
    elif fields == name_paper_key and paper_flag:
      max_len_new = max_length_paper

    label_tot_length = str(int(max_len_old) + int(max_len_new) +3) #+3 because of  ' | '
    formatting = '{0:^%ss}' % (label_tot_length)
  
    to_write += formatting.format( fields )
    
  file_report.write(to_write+"\n")

  #Write/format the values of each column
  for r, idx in enumerate(rowAscii_match):
    
    #Row numbers in FITS and ASCII of common clusters 
    clRow_fits = rowFits_match[r]
    clRow_ascii = idx #rowAscii_match[r]
    
    to_write = "\n"

    for tmp, fields in enumerate(ascii_keywds): 
      
      kwCol_fits = hdulist.data.names.index(fields)
      kwCol_ascii = ascii_keywds.index(fields)
	
      oldVal_fits = hdulist.data[clRow_fits][kwCol_fits]
      newVal_ascii = ascii_table[kwCol_ascii][clRow_ascii+1] #the '+1' correction is needed because of the additional HEADER line
          
      #Updates values...

      # Set undefined values to  '-' or -1.6375e+30
      if str(newVal_ascii).strip() in ['', '-', '-1.6375E+30', '-1.6375e+30']:
	#String
	if keys_form_unit[fields]['TFORM'].find('A') >=0 : newVal_ascii = '-'
	#Not string
	else : 	newVal_ascii = -1.6375e+30 

      if (fields in name_mass_key or fields in name_errMass_key) and newVal_ascii != -1.6375e+30:
	newVal_ascii = h_factor * float(newVal_ascii)
      
      max_len_new = length_new_field[tmp]
      
      if fields in fits_keywds:
	max_len_old = max(len(str(elem).strip()) for elem in fits_data[fields])
      else:
	max_len_old = max_len_new
      
      #if ALT_NAME has changed, write it in the report even if it is not an ASCII field
      if fields == name_altName_key and altName_flag:
	max_len_old = max([len(item) for item in old_altName_vec])
	max_len_new = max([len(item) for item in new_altName_vec])
	
	oldVal_fits = old_altName_vec[clRow_fits]
	newVal_ascii = new_altName_vec[clRow_fits]
	  
      elif fields == name_paper_key and paper_flag:
	max_len_new = max_length_paper
	
	oldVal_fits = fits_data[name_paper_key][clRow_fits]
	newVal_ascii = new_paper_vec[clRow_ascii]	
      
      formatting = ' {0:>%ss} | {1:<%ss} ' % (max_len_old, max_len_new)
      to_write += formatting.format(str(oldVal_fits), str(newVal_ascii))
	    
      #Update values for Boolean fields...
      if keys_form_unit[fields]['TFORM'] == 'L':
	if str(newVal_ascii).upper() in ["TRUE", "YES", "1.0"]: hdulist.data[clRow_fits][kwCol_fits] = True
	elif str(newVal_ascii).upper() in ["FALSE", "NO", "0.0", "", "NONE", "NULL", "[]", "{}"]: hdulist.data[clRow_fits][kwCol_fits] = False
      else:
	try:
	  hdulist.data[clRow_fits][kwCol_fits] = newVal_ascii
	except:
	  if str(newVal_ascii) == 'nan': hdulist.data[clRow_fits][kwCol_fits] = np.nan

    file_report.write(to_write)


#Write summary for NEW clusters (if any)
fits_keywds=[]
length_label_vec = []
Ncol_fits=int(hdulist.header['TFIELDS'])
for i in range(Ncol_fits):
  fits_keywds.append(hdulist.data.names[i])

if len(rowAscii_new) > 0: 
  file_report.write("\n\n# >>>> NEW CLUSTERS ** ADDED ** TO THE FITS TABLE <<<<\n\n")
  to_write = ""
  tmp = 0
  for fields in fits_keywds:
    
    format_tmp = coldefs.formats[tmp]
    tmp_length = ''
    
    if format_tmp.find('A') >= 0:
      tmp_length = format_tmp.split('A')[0]
    elif format_tmp.find('E') >= 0 or format_tmp.find('D') >= 0:
      tmp_length = '15' #For float and double, string size fixed to 15
    elif format_tmp.find('I') >= 0:
      index_fits_field = fits_keywds.index(fields)
      max_len_int =  len(str(fits_data[-1][index_fits_field]))
      tmp_length = str(max_len_int+3)
    elif format_tmp.find('L') >= 0:
      tmp_length = '6' #For boolean, string size fixed to 6
      
    length_label_vec.append( max( int(tmp_length), len(fields)+3 ) )
    
    formatting = '{0:^%ss}' % (length_label_vec[-1])
    
    to_write +=formatting.format( fields )
    tmp +=1
    
  file_report.write(to_write+"\n")

  j = 0

  for name in new_clNames:
    
    to_write = "\n"
    for k, field in enumerate(fits_keywds):
      index_field = coldefs.names.index(field)
      format_field = coldefs.formats[index_field]

      kwCol_fits = fits_keywds.index(field)
      oldVal_fits = hdulist.data[Nrows_fits+j][kwCol_fits]	# Add rows after the last one, filling the empty ones...
      
      if field in ascii_keywds:
	kwCol_ascii = ascii_keywds.index(field)      
	
	newVal_ascii = ascii_table[kwCol_ascii][rowAscii_new[j]+1]
	
	if format_field.find('A') >= 0 and (newVal_ascii.strip()).upper() in ['', '-', "NULL", "NAN", "NONE", "FALSE"]: newVal_ascii = '-'
	elif str(newVal_ascii).strip() in ['-1.6375E+30', '-1.6375e+30']:  newVal_ascii = -1.6375e+30
	if (fields in name_mass_key or fields in name_errMass_key) and newVal_ascii != -1.6375e+30:
	  newVal_ascii = h_factor * float(newVal_ascii)
      else:
	oldVal_fits = hdulist.data[Nrows_fits+j][kwCol_fits]
	
	if field == name_index_key:
	  #The INDEX associated with the new clusters are created by adding +1 to the previous value
	  newVal_ascii = 1 + hdulist.data[Nrows_fits+j-1][kwCol_fits]
	  
	elif field == name_catalog_key:
	  newVal_ascii = str(new_catalog)
	  
	#Galactic coordinates are created from RA, DEC (if any)
	elif field == 'GLON':
	  if len(ra_ascii) > 0 and len(dec_ascii)>0:  newVal_ascii = round(astCoords.convertCoords('J2000', 'GALACTIC', ra_ascii[rowAscii_new[j]], dec_ascii[rowAscii_new[j]], 2000)[0], 5)
	elif field == 'GLAT':
	  if len(ra_ascii) > 0 and len(dec_ascii)>0:  newVal_ascii = round(astCoords.convertCoords('J2000', 'GALACTIC', ra_ascii[rowAscii_new[j]], dec_ascii[rowAscii_new[j]], 2000)[1], 5)

	elif field == name_zErr_key:
	  newVal_ascii = np.nan
	elif field == name_zLimit_key:
	  newVal_ascii = np.nan
	elif field == name_paper_key:
	  newVal_ascii = tmp_new_paper
	elif format_field == 'L':
	  newVal_ascii = False
	elif field in name_coordinates_keys:
	  newVal_ascii = np.nan
	elif format_field == 'I':
	  newVal_ascii = -1
	elif format_field == 'E': #FLOAT
	  newVal_ascii = -1.6375E+30
	elif format_field.find("A") >= 0: #STRING
	  newVal_ascii = 'Null'

      #Change values...
      if format_field == 'L':
	if str(newVal_ascii).upper() in ["TRUE", "YES", "1.0"]: hdulist.data[Nrows_fits+j][kwCol_fits] = True
	elif str(newVal_ascii).upper() in ["FALSE", "NO", "0.0", "", "NONE", "NULL", "[]", "{}"]:  hdulist.data[Nrows_fits+j][kwCol_fits] = False
      else:  
	try:      
	  hdulist.data[Nrows_fits+j][kwCol_fits] = newVal_ascii   
	except:
	  if str(newVal_ascii) == 'nan': hdulist.data[Nrows_fits][kwCol_fits] = np.nan
	  else: print  '%s A problem occurred for cluster Name = %s : field = %s , value = %s \nAborted.\n' % (error, name, field, newVal_ascii); os._exit(0)
      
      formatting = '{0:^%ss}' % (length_label_vec[k])
      to_write += formatting.format( str(newVal_ascii) )
    j += 1
    file_report.write(to_write)


'''
  *** 4th data UPDATE: update the fits HEADER with the Version number and the creation date ***
'''

hdulist.header.add_comment("", before="TTYPE1")
version = raw_input("\n%s Please enter the Version number of the new table: " % question)

version_check = False
while version_check == False:
  try:
    if float(version): version_check = True
  except  ValueError:
    print bcolors.FAIL+ "\n\t\t*** Version number not valid ***" + bcolors.ENDC
    version = raw_input("\n\t-> Please enter a valid version number: ")

hdulist.header.add_comment("*** Version " +str(version)+" ***", before="TTYPE1")

today = date.today().strftime("%A %d. %B %Y")
comment = "*** Compiled at IDOC/IAS on %s ***" % (today)
hdulist.header.add_comment(comment, before="TTYPE1")

hdulist.header.add_comment("", before="TTYPE1")
extname = raw_input("\n%s Please enter the name of the new FITS table (without extension): " % question)
hdulist.header.update('EXTNAME', extname, before='TTYPE1')

#The new fits table is written in a temporary file, which will be deleted after the proper 'undef' values will be set
hdulist.writeto('new_table.fits')

file_report.close()

#Reopen the temporary fits table to change the undefined values (e.g., -1.6375E+30) to 'NULL' or NaN
hdulist = pyfits.open('new_table.fits')
fits_header = hdulist[1].header
fits_data = hdulist[1].data

command = "rm new_table.fits"
os.system(command)

Ncol_fits = int(fits_header['TFIELDS'])
Nrows_fits = fits_header['NAXIS2']

#Dictionary defining 'undef' values for different kind of fields
_UNDEF_VALUES_ = {
  'FLOAT' : {np.nan},
  'INT' : {-1},
  'STRING' : {'NULL'},
  name_zType_key : {'undef'},
  'PIPELINE' : {0},
  'PIPE_DET' : {0}
  }

'''
  *** 5th data UPDATE: set the proper 'undef' values for the different fields ***
'''

hdulist[1].data = set_undef_values(fits_data)

file_output = extname+'.fits'
print "\n\t>> New updated file:" + bcolors.OKGREEN + " %s " % (file_output) + bcolors.ENDC
print "\t>> Details of the applied updates are reported in:" + bcolors.OKGREEN + " %s " % (file_report_name) + bcolors.ENDC + "\n"
hdulist.writeto(file_output)
