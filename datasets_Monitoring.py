#! /usr/bin/python

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
This is a script aimed at monitoring the status of the Sitools2 datasets
and the mapping of their fields.

Put the script in the Sitools2 folder data/datasets(/map, for the latest versions)
where the datasets information are stored as xml files. 
Then, read and record the current status/mapping, with:

$ datasets_Monitoring --record 

The datasets properties are locally stored in files named as:

        <dataset_name>.lastStatus.xml

The '--record' option should be executed manually by the administrator every time 
one or more datasets are modified (it would be good to add a reminder to the 
Sitools2 pop-up message). 

To check the datasets mapping/status, launch the script with the '--check' option:

$ datasets_Monitoring --check 

This performs a consistency check between the current (int@*.xml or map/string@*.xml) 
and the last recorded status (<dataset_name>.lastStatus.xml).
If any inconsistency is found, an alert e-mail is sent.

The '--check' option should be run daily and automatically by the system.

@author: Alessandro NASTASI for IAS -IDOC
@date: 27/04/2015
'''

__author__ = "Alessandro Nastasi"
__credits__ = ["Alessandro Nastasi", "Herve' Ballans"]
__license__ = "GPL"
__version__ = "1.0"
__date__ = "27/04/2015"

import sys,os, time
from datetime import date
import xml.etree.ElementTree as ET
import smtplib
from email.mime.text import MIMEText

sitools2_xml_filenames = "string@*.xml"                   		## Files where Sitools stores datasets information
file_path='/usr/local/Sitools2_SZ_Cluster_DB/data/datasets/map/' 	## Path where the (string@*.xml) sitools files are stored

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

_ERROR_CODE = {
    1:'Status inconsistency found:',
    2:'Mapping inconsistency found:',
    3:"The *.lastStatus.xml files were probably not updated: re-run the script with '--record' option."
              }

def create_id_alias_dict(xml_root):
    ## Column dictionary " column_id : column_alias ". No mapping information here.
    id_alias_dict = {}
    for col in xml_root.findall('column'): 
        column_id = col.find('id').text
        column_alias = col.find('columnAlias').text
        id_alias_dict[column_id] = column_alias
        
    return id_alias_dict
    
    
def send_alert_mail(body):     
    SMTP_SERVER = 'smtp.ias.u-psud.fr'
    SMTP_PORT = 25
     
    sender = 'sitools2.notifier@ias.u-psud.fr'
    #password = ''
    recipient = 'sitools2@ias.u-psud.fr'
    subject = '[Sitools2 - SZDB] Datasets status ALERT'
         
    headers = ["From: "+sender,
               "Subject: " + subject,
               "To: " + recipient,
               "MIME-Version: 1.0",
               "Content-Type: text/html"]
    headers = "\r\n".join(headers)
     
    session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
     
    #session.ehlo()
    #session.starttls()
    #session.ehlo
    #session.login(sender, password)
        
    body = MIMEText(body, 'html')
    session.sendmail(sender, recipient, headers + "\r\n\r\n" + body.as_string())
    session.quit()

def record_status():
    print "\n> Recording current datasets properties ...\n"
    
    command = "ls "+file_path+sitools2_xml_filenames
    intXml_list = os.popen(command).readlines()
    
    for item in intXml_list:
        item=item.strip()
        
        tree = ET.parse(item)
        root = tree.getroot()
    
        dataset_name = root.find('name').text
        fileDataset = file_path+dataset_name+'.lastStatus.xml'
        fileOut = open(fileDataset, 'w')
    
        ##Header in recorded file
        today = date.today().strftime("%A %d. %B %Y")
        towrite = "<!--File recorded on "+str(today)+"-->\n"
        fileOut.write(towrite)
    
        ##Record the last status of the Dataset
        towrite = "<dataset>\n"
        fileOut.write(towrite)
        towrite = "<!--Last Dataset status:-->\n"
        fileOut.write(towrite)
        status = root.find('status').text
        fileOut.write(" <lastStatus>"+status+"</lastStatus>")

        ## Column dictionary " column_id : column_alias ". No mapping information here.            
        column = create_id_alias_dict(root)
        
        ## Num of mapped concepts
        mapped_Concepts_Id = []
        mapped_Column_Id = []    
        for elem in root.findall('conceptId'): mapped_Concepts_Id.append(elem.text)
        for elem in root.findall('columnId'): mapped_Column_Id.append(elem.text)
            
        num_mapped_Concepts = len(mapped_Concepts_Id)
        
        ## Record the last mapping
        ## Num of last mapped concepts
        towrite = "\n<!--Last mapping:-->\n <!--mappedColumns-->\n"
        fileOut.write(towrite)
        towrite = " <totNum>"+str(num_mapped_Concepts)+"</totNum>\n"
        fileOut.write(towrite)
        
        for i,item in enumerate(mapped_Column_Id):
            towrite=" <columnId>"+str(item)+"</columnId>\n"
            fileOut.write(towrite)
            towrite=" <columnAlias>"+str(column[item])+"</columnAlias>\n"
            fileOut.write(towrite)
            towrite=" <conceptId>"+str(mapped_Concepts_Id[i])+"</conceptId>\n"
            fileOut.write(towrite)
      
        fileOut.write(" <!--/mappedColumns-->\n</dataset>")
        fileOut.close()
        print "   - Current status and mapping of %s written in %s\n" % (dataset_name, fileDataset)

def check_status():
    
    today = date.today().strftime("%A %d. %B %Y")
    now = time.strftime("%H:%M:%S")
    check_datime = today +' at '+ now
    print "\n#\n#Last check done on", check_datime,"\n#"
    print "\n> Checking datasets properties ..."
    command = "ls "+file_path+sitools2_xml_filenames
    intXml_list = os.popen(command).readlines()
    error_status, error_mapping, warning = False, False, False
    email_body = "<br></br><i>Outcome of the datasets check done on %s</i>" % check_datime
    for item in intXml_list:
        item=item.strip()
        email_body+= "\n"
        tree = ET.parse(item)
        currentRoot = tree.getroot()
  
        dataset_name = currentRoot.find('name').text
        filename_dataset = file_path+dataset_name+'.lastStatus.xml'
        print "\n   - ",dataset_name

        tree = ET.parse(filename_dataset)
        lastRoot = tree.getroot()

        #Start the check ...

        ##************  Status  ************##

        lastStatus = lastRoot.find('lastStatus').text
        currentStatus = currentRoot.find('status').text
        output_check = True
        showStatus = ""
        output_message = ""

        if lastStatus != currentStatus:
            if currentStatus == 'INACTIVE':
                output_check = bcolors.FAIL+"[FAIL]"+bcolors.ENDC
                output_message =  "\n     "+bcolors.FAIL+_ERROR_CODE[1]+bcolors.ENDC
                output_message += "\n     Current status: "+bcolors.FAIL+currentStatus+bcolors.ENDC+" -  last status: "+bcolors.FAIL+lastStatus+bcolors.ENDC
                email_body+="<h3>"+dataset_name+"</h3><b>*** "+_ERROR_CODE[1]+" ***</b><p>Current status: <b>"+currentStatus+"</b> , last status: <b>"+lastStatus+"</b>."
            else:
                warning = True
                output_check = bcolors.WARNING+"[FAIL]"+bcolors.ENDC
                output_message =  "\n     "+bcolors.WARNING+_ERROR_CODE[1]+bcolors.ENDC
                output_message += "\n     Current status: "+bcolors.WARNING+currentStatus+bcolors.ENDC+" -  last status: "+bcolors.WARNING+lastStatus+bcolors.ENDC
                email_body+="<h3>"+dataset_name+"</h3><b>"+_ERROR_CODE[1]+"</b><p>Current status: <b>"+currentStatus+"</b> , last status: <b>"+lastStatus+"</b>."
                
            error_status = True
            showStatus=""                
            
        else: 
            output_check = bcolors.OKGREEN+"[OK]"+bcolors.ENDC
            showStatus="   -   "+currentStatus
        
        print '   {0:20s} {1:7s}'.format('Status check ...', output_check)+showStatus+output_message
            

        ##************  Mapping  ************##

        ## Last mapped concepts
        #num_last_mapped_Concepts = int(lastRoot.find('totNum').text)
        last_current_mapped_Column_Id = []
        for elem in lastRoot.findall('columnId'): last_current_mapped_Column_Id.append(elem.text)
        
        ## Current mapped concepts
        current_mapped_Column_Id = [] 
        for elem in currentRoot.findall('columnId'): current_mapped_Column_Id.append(elem.text)
            
        output_check = ""
        
        ## Find the columns that lost the mapping
        # Create dictionary from current mapping - this does not change from last/current files
        column = create_id_alias_dict(currentRoot)            

        # Columns mapped in the last file, but not in the current one --> Mapping lost!
        missing_current_columnAlias = [column[columnId] for columnId in last_current_mapped_Column_Id if columnId not in current_mapped_Column_Id]
        # Columns mapped in the current file, but not in the last one --> User's error: *.lastStatus.xml probably not updated
        missing_last_columnAlias = [column[columnId] for columnId in current_mapped_Column_Id if columnId not in last_current_mapped_Column_Id]

        output_message = ""

        if len(missing_current_columnAlias) == 0 and len(missing_last_columnAlias) == 0:
            output_check = bcolors.OKGREEN+"[OK]"+bcolors.ENDC
        elif len(missing_last_columnAlias) > 0:
            warning = True
            output_check = bcolors.WARNING+"[FAIL]"+bcolors.ENDC
            output_message =  "\n     "+bcolors.WARNING+_ERROR_CODE[2]+bcolors.ENDC
            output_message += "\n     Some columns are mapped in the new version, but not in the last one: "+bcolors.WARNING+str(missing_last_columnAlias)+bcolors.ENDC
            email_body += "<h3>"+dataset_name+"</h3><b>"+_ERROR_CODE[2]+"</b><p> Some columns are mapped in the new version, but not in the last one: "+str(missing_last_columnAlias)+"</p>"
        elif len(missing_current_columnAlias) > 0 and len(missing_last_columnAlias) == 0:
            output_check = bcolors.FAIL+"[FAIL]"+bcolors.ENDC
            output_message =  "\n     "+bcolors.FAIL+_ERROR_CODE[2]+bcolors.ENDC
            output_message += "\n     The following column(s) is(are) not mapped anymore: "+bcolors.FAIL+str(missing_current_columnAlias)+bcolors.ENDC
            email_body += "<h3>"+dataset_name+"</h3><b>*** "+_ERROR_CODE[2]+" ***</b><p> The following column(s) is(are) not mapped anymore: <b>"+str(missing_current_columnAlias)+"</b></p>"

            error_mapping = True
            
        print '   {0:20s} {1:7s}'.format('Mapping check ...', output_check)+output_message

    print "\n__________________________________________________\n\n> Outcome of the check process:"
    email_body += "<p>__________________________________________________</p><p>The check process has produced the following message:"
    
    ## Send an e-mail alert if any error/inconsistency is found
    if error_status or error_mapping or warning:
        if warning:
            print "\n   "+bcolors.WARNING+_ERROR_CODE[3]+bcolors.ENDC
            email_body += "<p></p><i><h4>"+_ERROR_CODE[3]+'</h4></i></p>'
        else:
            print bcolors.FAIL+'\n   Unexpected errors have been found! Please check the datasets properties in Sitools2.'+bcolors.ENDC
            email_body += "<p></p><h4>Unexpected errors have been found! Please check the datasets properties in Sitools2.</h4></br></p>"
            
        send_alert_mail(email_body)            
        print "\n\t>> !! ALERT E-MAIL SENT !! <<\n"           

	#The alert mail text is stored in an *log.html file for keeping track of the found errors
        errors_log_name = file_path+'monitoring_errors.log.html'
        errors_log_file = open(errors_log_name, 'a')
        errors_log_file.write(email_body)
        errors_log_file.close()

    else:
        print bcolors.OKGREEN+'\n   No errors/inconsistencies found.\n'+bcolors.ENDC


            
if (len(sys.argv) > 1):
    option = sys.argv[1]
    if option=='--check': check_status()
    elif option=='--record':
        overwrite = raw_input(bcolors.WARNING+"\n  This option will overwrite the current recorded settings. Do you really want to proceed?:  "+ bcolors.ENDC)
        if overwrite in ["Yes","yes","Y","y","oui", "OUI", "Oui"]: record_status()
        elif overwrite in ["No","no","N", "n"]: 
            print "Aborted.\n"
            exit(0)
    else:
        print bcolors.WARNING +  "\n> Sintax:\t$ python dataset_Monitoring.py [OPTION]\n" + bcolors.ENDC
        print "Options:\n\n   --check\n\tA status consistency check is performed between the current and last recorded datasets properties."
        print "\n   --record\n\tThe current datasets properties (status and mapping) are recorded. NB. This procedure will overwrite the previously recorded entries.\n"
        exit(0)
