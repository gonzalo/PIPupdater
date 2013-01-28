#! /usr/bin/env python
import pdb
import argparse
import oauth2
import ConfigParser
import datetime
import os
import re
import smtplib
import sys
import time
from time import strftime
import twitter
import urllib2
import xmpp


import googleoauth2


# TODO(soon) integrate googleoauth2
# TODO check if config read fails
# TODO check conditions to resend email or IM
# TODO include header (author, web...)
# TODO doc functions
# TODO generate a log

# CONFIG BLOCK #

# list of potencial config locations
# from lower to higher priority
CONFIG_FILES = ["/etc/PIPupdater/PIPupdater.conf",
                os.path.expanduser("~/.PIPupdater/PIPupdater.conf"),
                "PIPupdater.conf"]

# regular expression for address
ADDRESS_REGEXP = re.compile('(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'\
                            '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'\
                            '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'\
                            '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')

# GLOBAL VARS
# Default values

MODE_VERBOSE = False
MODE_EMAIL   = False
MODE_IM      = False
MODE_TWITTER = False
MODE_DEBUG   = False

# FUNCTIONS

def args_parser():
    global MODE_VERBOSE
    global MODE_EMAIL
    global MODE_IM
    global MODE_TWITTER
    global MODE_DEBUG

    parser = argparse.ArgumentParser(description='Use web services to '\
                                                 'monitorize your WAN IP')

    #setting modes
    parser.add_argument("-v", "--verbose", 
            help="enable verbose mode "\
                 "(enabled if no other output has been selected)",
            action="store_true")
    parser.add_argument("-m", "--mail", 
            help='send email when IP is updated '\
                 '(requires configure smtp)',
            action="store_true")
    parser.add_argument("-im", "--instant", 
            help="send IM when IP is updated "\
                 "(requires XMPP/Jabber/gaccount)",
            action="store_true")
    parser.add_argument("-t", "--twitter", 
            help="send DM tweet when IP is updated "\
                 "(requires register app)",
            action="store_true")
    parser.add_argument("-d", "--debug", 
            help="enable debug mode (enables verbose mode also)",
            action="store_true")

    args_parsed = parser.parse_args()
    
    if args_parsed.verbose: MODE_VERBOSE = True
    if args_parsed.mail:    MODE_EMAIL   = True
    if args_parsed.instant: MODE_IM      = True
    if args_parsed.twitter: MODE_TWITTER = True
    if args_parsed.debug:   
        #MODE_DEBUG also enables MODE_VERBOSE
        MODE_DEBUG   = True
        MODE_VERBOSE = True
        
    #TODO find a better way to do this
    #default mode if no other output has been selected
    if not (args_parsed.mail or args_parsed.instant \
            or args_parsed.twitter): MODE_VERBOSE = True

    return args_parsed

def read_config_file(config_files):

    if MODE_DEBUG: print "Loading config file(s): %s" % config_files

    try:
        config = ConfigParser.ConfigParser()
        if config.read(config_files)==[]:
            print "Error: no config file found!"
            sys.exit(-1)

    except:
        print "Error parsing config file"
        sys.exit(-1)

    return config

def get_ip(web_service_providers):

    result = None
    for web_service_url in web_service_providers:
        try:
            if MODE_DEBUG: 
                print "Trying to retrieve IP using service: %s" % \
                      web_service_url
            response = urllib2.urlopen(web_service_url).read()
            result = ADDRESS_REGEXP.search(response)
        except IOError, e:
            if hasattr(e, 'reason'):
                print 'Failed to reach a server.'
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
        except:
            print "Unexpected error:", sys.exc_info()[0]
            return None
        if result != None: break

    if result:
        return result.group()
    else:
        return None

def get_date_time():
    return strftime("%Y-%m-%d %H:%M:%S")

def send_mail(mail_text, email_config):

    #TODO test if config fails
    smtp_server = email_config['smtp_server']
    smtp_port   = int(email_config['smtp_port'])
    use_oauth2  = bool(email_config['use_oauth2'])
    
    #TODO improved connection testings, manage SMTP exceptions
    try:
        if MODE_DEBUG: print "Connecting to smtp server"

        # openning connection with 
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()

        # connect gmail server using OAuth2 or...
        if use_oauth2:
            server.starttls()
            server.ehlo()
            if MODE_DEBUG: print "Requesting access token"
            access_token = googleoauth2.RefreshToken(
                email_config['client_id'], 
                email_config['client_secret'], 
                email_config['refresh_token']
                )['access_token']
            if MODE_DEBUG: print "Access token = %s" % access_token
            oauth2_string  = googleoauth2.GenerateOAuth2String(
                email_config['google_user'],
                access_token)
            if MODE_DEBUG: print "OAuth2_string = %s" % oauth2_string
            server.docmd('AUTH', 'XOAUTH2 ' + oauth2_string)
        # connect STMP server using standar methods                    
        else:
            starttls_required = bool(email_config['starttls'])
            if starttls_required: 
                server.starttls()
                server.ehlo()
            server.login(email_config['username'], email_config['password'])

        # once indentified send email
        server.send_mail(email_config['from_address'], 
                         email_config['to_address'], 
                         mail_text)
        server.quit()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        return False

    return True

def compose_mail(email_config, host_name, ip):

    subject = 'Current IP address for %s is: %s' % (host_name, ip)
    msg = 'Current IP address for <b>%s</b> is: <b>%s</b>' % (host_name,ip)

    mail_text  = ("From: %s <%s>\r\n"% (
            email_config['from_name'], 
            email_config['from_address']))
    mail_text += ("To: %s <%s>\r\n"    % (
            email_config['to_name'], 
            email_config['to_address']))
    mail_text += ("Subject: %s\r\n" % (subject))
    mail_text += ("Content-Type: text/html\r\n")
    mail_text += ("\r\n")
    mail_text += msg
    return mail_text

def send_im(text, xmpp_config):
    try:
        jid = xmpp.protocol.JID(xmpp_config['username'])

        if MODE_DEBUG:
            client = xmpp.Client(jid.getDomain(), debug=['always']) 
        else: 
            client = xmpp.Client(jid.getDomain(), debug=[]) 

        client.connect(server=(xmpp_config['xmpp_server'],
                        int(xmpp_config['xmpp_port'])))
        client.auth(jid.getNode(),xmpp_config['password'])    
        client.send(xmpp.protocol.Message(xmpp_config['receiver'], text))
        return True
    except:
        return False

def send_tweet(text, twitter_config):

    if twitter_config['send_as_dm']: 
        text = "d %s %s" % (twitter_config['receiver'], text)
    try:
        api = twitter.Api(consumer_key=twitter_config['consumer_key'],
                consumer_secret=twitter_config['consumer_secret'],
                access_token_key=twitter_config['access_token'],
                access_token_secret=twitter_config['access_token_secret'])
        status = api.PostUpdate(text)

        return True
    except twitter.TwitterError, e:
        print e.message
        return False
    except:
        print "Unexpected error:", sys.exc_info()[0]
        return False

## MAIN DEF ##

def main():
    args_parser()
    last_external_ip = None

    config = read_config_file(CONFIG_FILES)

    try:
        main_config    = config._sections['Main']
        email_config   = config._sections['Email config']
        xmpp_config    = config._sections['XMPP config']
        twitter_config = config._sections['Twitter config']

        time_interval = int(main_config['time_interval'])
        web_service_providers = main_config['web_service_providers'].split(',')
    except:
        print "Error parsing config file"
        sys.exit(-1)

    host_name = os.uname()[1]
    ## START LOOP BLOCK ##
    while True:

        external_ip = get_ip(web_service_providers)

        if external_ip == None:
            print "%s %s: Unable to retrieve external IP. "\
                  "Next attempt in %d seconds" % (
                  get_date_time(), 
                  host_name,
                  time_interval)
        else:
            #Compare current IP with previous, do tasks if has been updated
            if external_ip != last_external_ip:

                last_external_ip = external_ip
            
                #Display at screen if required
                if MODE_VERBOSE: 
                    print "%s %s %s: IP updated. Next check on %d seconds" % (
                        get_date_time(), 
                        host_name,
                        external_ip,
                        time_interval)

                #Send email if required
                if MODE_EMAIL:
            
                    mail_text = compose_mail(email_config, 
                                             host_name, 
                                             external_ip)

                    if MODE_DEBUG: 
                        print "Trying to send email"
                        print "========= Mail text begin ========="
                        print mail_text
                        print "========== Mail text end =========="
                        print 

                    mail_sent = send_mail(mail_text, email_config)

                    if mail_sent:
                        if MODE_DEBUG: print "Email sent"
                    else:
                        #reset last_external_ip to force email during next check
                        last_external_ip = None
                        if MODE_DEBUG: print "ERROR: Email not sent"

                #Send IM if required
                if MODE_IM:

                    message = '%s - Current IP address for %s is: %s' % (
                                get_date_time(),
                                host_name, 
                                external_ip)
                    if MODE_DEBUG: print "Trying to send IM"

                    im_sent = send_im(message, xmpp_config)
            
                    if im_sent:
                        if MODE_DEBUG: print "IM sent"
                    else:
                        #reset last_external_ip to force IM during next check
                        last_external_ip = None
                        if MODE_DEBUG: print "ERROR: IM not sent"

                #Send tweet if required
                if MODE_TWITTER:

                    message = '%s - Current IP address for %s is: %s' % (
                                get_date_time(),
                                host_name, 
                                external_ip)
                    if MODE_DEBUG: print "Trying to send tweet"

                    im_sent = send_tweet(message, twitter_config)
            
                    if im_sent:
                        if MODE_DEBUG: print "Tweet sent"
                    else:
                        #reset last_external_ip to force IM during next check
                        last_external_ip = None
                        if MODE_DEBUG: print "ERROR: tweet not sent"
                        

            #do nothing if IP is updated
            else:
                if MODE_VERBOSE: 
                    print "%s %s %s: Nothing to do. Next check on %d seconds" \
                        % (
                        get_date_time(), 
                        host_name,
                        external_ip,
                        time_interval)

        #now rest a while
        try:
            time.sleep(time_interval)
        except KeyboardInterrupt:
            print "Program stopped by user"
            sys.exit()

## END MAIN DEF ##

if __name__ == '__main__':
    main()

