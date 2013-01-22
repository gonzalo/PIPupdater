#! /usr/bin/env python

import argparse
import datetime
import os
import re
import smtplib
import sys
import time
from time import strftime
import urllib2

#import oauth2.py
import oauth2

# TODO 
# - include header (author, web...)
# - generate a log

# CONFIG BLOCK #

# time interval between checks (seconds)
time_interval = 10

# email parameters
from_name =    "PIPupdater"
from_address = "gonzalo.cao@gmail.com"
to_name =      "Destiny name"
to_address  =  "gonzalo.cao@gmail.com"

# Gmail options

# You have two options to use your gmail account with 

# Option A) 
# Type your user and password (insecure)
username = 'your_google_user'
password = 'your_google_password'

# Option B) Gmail OAUTH2 parameters
# 1. Register your application with https://code.google.com/apis/console/
# 2. Copy client_id and client_secret values below
# 2. Run this command in app directory and follow instructions
#    $ python oauth2.py --generate_oauth2_token --client_id=your_client_id  --client_secret=your_client_secret
# 3. Copy refresh_token value below

google_user   = "your_user@gmail.com"
client_id     = "your_client_id.apps.googleusercontent.com"
client_secret = "your_client_secret"
refresh_token = "your_refresh_token"

# Web services to check IP
# You can use any of this providers
ip_checker_url = "http://checkip.dyndns.org/"
#ip_checker_url = "http://my-ip-address.com/"
#ip_checker_url = "http://ip.nefsc.noaa.gov/"
#ip_checker_url = "http://www.ipaddrs.com/"
#ip_checker_url = "http://www.my-ipaddress.org/"

# regular expression for address
address_regexp = re.compile('(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')

# GLOBAL VARS
# Default values

MODE_VERBOSE = False
MODE_EMAIL   = False
MODE_DEBUG   = False

# FUNCTIONS

def argsParser():
	global MODE_VERBOSE
	global MODE_EMAIL
	global MODE_DEBUG

	parser = argparse.ArgumentParser(description='Use web services to monitorize your WAN ')

	#setting modes
	parser.add_argument("-v", "--verbose", 
			help="enable verbose mode (enabled if no other output has been selected)",
			action="store_true")
	parser.add_argument("-m", "--mail", 
			help="send email when IP is updated (requires smtp email account)",
			action="store_true")
	parser.add_argument("-d", "--debug", 
			help="enable debug mode (enables verbose mode also)",
			action="store_true")

	args = parser.parse_args()
	
	if args.verbose: MODE_VERBOSE = True
	if args.mail:    MODE_EMAIL   = True
	if args.debug:   
		MODE_DEBUG   = True
		MODE_VERBOSE = True

	#default mode if no other output has been selected
	if not (args.verbose or args.mail): MODE_VERBOSE = True

	return args


def getIP():
	#TODO improve errors detection
	try:
		response = urllib2.urlopen(ip_checker_url).read()
		result = address_regexp.search(response)
	except:
		print "Unexpected error:", sys.exc_info()[0]
		return None

	if result:
		return result.group()
	else:
		return None

def getDateTime():
	return strftime("%Y-%m-%d %H:%M:%S")

def sendMail_GMail(mail_text):

	#TODO improved connection testings
	#TODO allow direct login or oauth2 login
	try:
		if MODE_DEBUG: print "Connecting to google server"
		server = smtplib.SMTP('smtp.gmail.com:587')
		server.ehlo()
		server.starttls()
		server.ehlo()
		#server.login(username,password)

		if MODE_DEBUG: print "Requesting access token"
		access_token = oauth2.RefreshToken(client_id, client_secret, refresh_token)['access_token']
		if MODE_DEBUG: print "Access token = %s" % access_token

		oauth2_string  = oauth2.GenerateOAuth2String(google_user, access_token)
		if MODE_DEBUG: print "OAuth2_string = %s" % oauth2_string

		server.docmd('AUTH', 'XOAUTH2 ' + oauth2_string)
		server.sendmail(from_address, to_address, mail_text)
		server.quit()
	except:
		print "Unexpected error:", sys.exc_info()[0]
		return False

	return True

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
last_external_ip = None

## START LOOP BLOCK ##
while True:

	host_name = os.uname()[1]
	external_ip = getIP()

	if external_ip==None:
		print "%s %s: Unable to retrieve external IP. Next attempt in %d seconds" % (
			getDateTime(), 
			host_name,
			time_interval)
	else:
		#Compare current IP with previous, do tasks if has been updated
		if external_ip != last_external_ip:

			last_external_ip = external_ip
		
			#Display at screen if required
			if MODE_VERBOSE: 
				print "%s %s %s: IP updated, performing tasks. Next check on %d seconds" % (
					getDateTime(), 
					host_name,
					external_ip,
					time_interval)

			#Send email if required
			if MODE_EMAIL:
		
				mail_text = compose_mail(host_name, external_ip)

				if MODE_VERBOSE: 
					print "Trying to send email"
					print "========= Mail text begin ========="
					print mail_text
					print "========== Mail text end =========="
					print 

				mail_sent = sendMail_GMail(mail_text)

				if mail_sent:
					if MODE_VERBOSE: print "Email sent"
				else:
					#reset last_external_ip to force email during next check
					last_external_ip = None
					if MODE_VERBOSE: print "ERROR: Email not sent"
					

		#do nothing if IP is updated
		else:
			if MODE_VERBOSE: 
				print "%s %s %s: Nothing to do. Next check on %d seconds" % (
					getDateTime(), 
					host_name,
					external_ip,
					time_interval)

	#now rest a while
	try:
		time.sleep(time_interval)
	except KeyboardInterrupt:
		print "Program stopped by user"
		sys.exit()

## END LOOP BLOCK ##









