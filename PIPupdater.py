import argparse
import os
import re
import smtplib
import time
import urllib2

# TODO 
# - include header (author, web...)
# - include help and instructions
# - create GIT repository
# - prepare fo
# - generate a log

# CONFIG BLOCK #

# time interval between checks (seconds)
time_interval = 600

# email parameters
from_name =    "PIPupdater"
from_address = "from_address@gmail.com"
to_name =      "User name"
to_address  =  "to_address@gmail.com"

# Credentials 
# TODO hide this stuff
username = 'your_gmail_user'
password = 'your_gmail_pass'

# web service
ip_checker_url = "http://checkip.dyndns.org/"

# regular expression for address
# TODO improve regular expression
address_regexp = re.compile ('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')


# TODO check arguments at least one action required
def argsParser():
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", 
			help="enable verbose mode",
			action="store_true")
	parser.add_argument("-m", "--mail", 
			help="send email",
			action="store_true")

	args = parser.parse_args()
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

def sendMail_GMail(mail_text):

	#TODO verify if connection goes wrong
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(username,password)
	server.sendmail(from_address, to_address, mail_text)
	server.quit()

def compose_mail(host_name, ip):

	msg_template = 'Current IP address for %s is: %s' % (host_name, ip)

	mail_text  = ("From: %s <%s>\r\n"% (from_name, from_address))
	mail_text += ("To: %s <%s>\r\n"	% (to_name, to_address))
	mail_text += ("Subject: %s\r\n" % (msg_template))
	#TODO MSG BODY EMPTY
	mail_text += msg_template
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
			if args.verbose:
				print "IP address updated. Host: %s IP: %s" % (host_name, external_ip)

			#Send email if required
			if args.mail:
		
				mail_text = compose_mail(host_name, external_ip)

				if args.verbose: 
					print "Trying to send email"
					print "Mail text =\r\n%s" % mail_text

				sendMail_GMail(mail_text)

				if args.verbose: print "Email sent"

	#now rest a while
	time.sleep(time_interval)

## END LOOP BLOCK ##









