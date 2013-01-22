#! /usr/bin/env python

import argparse
import datetime
import os
import re
import smtplib
import time
from time import strftime
import urllib2

# TODO 
# - include header (author, web...)
# - include help and instructions
# - generate a log

# CONFIG BLOCK #

# time interval between checks (seconds)
time_interval = 10

# email parameters
from_name =    "PIPupdater"
from_address = "your_gmail_email"
to_name =      "Destiny name"
to_address  =  "to_address@domain.com"

# Credentials 
# TODO hide this stuff
username = 'your_gmail_user'
password = 'your_gmail_pass'

# web service
# this providers work without any changes
ip_checker_url = "http://checkip.dyndns.org/"
#ip_checker_url = "http://my-ip-address.com/"
#ip_checker_url = "http://ip.nefsc.noaa.gov/"
#ip_checker_url = "http://www.ipaddrs.com/"
#ip_checker_url = "http://www.my-ipaddress.org/"

# promising but need some changes
#ip_checker_url = "http://www.hostip.info/"
#ip_checker_url = "http://whatismyipaddress.com/"
#ip_checker_url = "http://findwhatismyipaddress.org/"
#ip_checker_url = "http://www.whatsmyip.org/"
#ip_checker_url = "http://www.ip-adress.com/"


# regular expression for address
# simple regexp - from 0.0.0.0 to 999.999.999.999
# address_regexp = re.compile ('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
# improved regexp from 0.0.0.0 to 255.255.255.255
address_regexp = re.compile('(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')

# GLOBAL VARS
# Default values

MODE_VERBOSE = False


# TODO check arguments at least one action required
def argsParser():
	global MODE_VERBOSE

	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", 
			help="enable verbose mode",
			action="store_true")
	parser.add_argument("-m", "--mail", 
			help="send email",
			action="store_true")

	args = parser.parse_args()
	

	if args.verbose: MODE_VERBOSE = True

	return args


def getIP():
	#TODO improve error detection, use try...
	# sample?
	#try:
	#	ipurl = "http://" + iphost + Ugate_page
	#	urlfp = urllib.urlopen(ipurl)
	#	ipdata = urlfp.read()
	#	urlfp.close()
	#except:
	#	logline = "No address found on router at " + iphost
	#	logger.logexit(logline)
	#	sys.exit(-1)
	response = urllib2.urlopen(ip_checker_url).read()
	result = address_regexp.search(response)

	if result:
		return result.group()
	else:
		return None

def getDateTime():
	return strftime("%Y-%m-%d %H:%M:%S")

def sendMail_GMail(mail_text):

	#TODO verify if connection goes wrong
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(username,password)
	server.sendmail(from_address, to_address, mail_text)
	server.quit()

def compose_mail(host_name, ip):

	subject = 'Current IP address for %s is: %s' % (host_name, ip)
	msg = 'Current IP address for <b>%s</b> is: <b>%s</b>' % (host_name,ip)

	mail_text  = ("From: %s <%s>\r\n"% (from_name, from_address))
	mail_text += ("To: %s <%s>\r\n"	% (to_name, to_address))
	mail_text += ("Subject: %s\r\n" % (subject))
	mail_text += ("Content-Type: text/html\r\n")
	mail_text += ("\r\n")
	mail_text += msg
	return mail_text


## MAIN ##

args = argsParser()
last_external_ip = ""


## START LOOP BLOCK ##
while True:

	host_name = os.uname()[1]
	external_ip = getIP()

	if external_ip==None:
		print "Unable to retrieve external IP for %s" % host_name
	else:
		#Compare current IP with previous, do tasks if has been updated
		if external_ip != last_external_ip:

			last_external_ip = external_ip
		
			#Display at screen if required
			if MODE_VERBOSE:
				print "IP address updated. Host: %s IP: %s" % (
					host_name, external_ip)

			#Send email if required
			if args.mail:
		
				mail_text = compose_mail(host_name, external_ip)

				if MODE_VERBOSE: 
					print "Trying to send email"
					print "Mail text =\r\n%s" % mail_text

				sendMail_GMail(mail_text)

				if MODE_VERBOSE: print "Email sent"

	#now rest a while
	if MODE_VERBOSE: print "%s: Next update on %d seconds" % (getDateTime(), time_interval)
	time.sleep(time_interval)

## END LOOP BLOCK ##









