#!/usr/bin/env python3
'''
 VCS Configuration
 Create a read-only account on your VCS with API access
 NOTE: VCS must be running at least x7.2.1
 Format:
 vcs = (
     ['username', 'password', 'authentication_realm', 'base_uri', 'full uri to status.xml'],
 }
 
 To get the authentication_realm simply open the status.xml in your browser
 i.e. https://vcs.hostname.com/status.xml
 the authentication popup will include a string like
 "TANDBERG Video Communication Server xxxxxx" where x is the serial number
'''
vcs = (
    ['username', 'password', 'TANDBERG Video Communication Server XXXXXXXX', 'http://vcs1.hostname.com', 'http://vcs1.hostname.com/status.xml'],
    ['username', 'password', 'TANDBERG Video Communication Server XXXXXXXX', 'https://vcs2.hostname.com', 'https://vcs2.hostname.com/status.xml'],
)
# SMTP server configuration
smtpsrv = "my.smtphost.com"					# smtp host
destadd = "destination.email@address.com".split()		# email destination - don't remove the .split()
fromadd = "source.email@address.com"				# email source

import urllib.request, urllib.error, re, sys, smtplib, string
from xml.dom.minidom import parseString
def stream (username, password, vcsrealm, vcs_buri, vcs_furi):
    'connect to cisco video communication server'
    auth_handler = urllib.request.HTTPBasicAuthHandler()
    auth_handler.add_password(realm=vcsrealm,
                       uri=vcs_buri,
                       user=username,
                       passwd=password)
    opener =  urllib.request.build_opener(auth_handler)
    urllib.request.install_opener(opener)
    res = opener.open(vcs_furi)
    nodes = res.read()
    return nodes
def stripxml (xml):
    'strip XML tagging'
    regex = '<[^<]+>'
    r1 = (re.sub(regex, ':::', xml))
    r2 = (r1.split(':::'))
    r3 = [x for x in r2 if x != '']
    da = 3
    ad = ([])
    while da < len(r3):
        for i in range(0, len(r3), 3):
            ad.append (r3[i:i + 3])
        po = len(r3) / 2
        da *= int(po)
    return ad
def getalarmdetail (xml):
    'parse stripped xml'
    parseme = stripxml(xml)
    x = ''
    c = 0
    for i in enumerate(parseme):
        if i[1][2] == 'Acknowledged':
            continue
        if i[1][2] == 'Unacknowledged':
            c += 1
        elif i[1][2] == 'Raised':
            c += 1
        u = 'ID: ' + str(i[1][0])
        u = u + '\nDescription: ' + str(i[1][1])
        u = u + '\nState: ' + str(i[1][2])
        u = u + '\n'
        x = ("%s%s\n" % (x, u))
    if x == '':
        return str(x)
    x = x + '\nPlease login to ' + vcs_buri + ' to investigate'
    return (c, str(x))
for o in vcs:
    username = o[0]
    password = o[1]
    vcsrealm = o[2]
    vcs_buri = o[3]
    vcs_furi = o[4]
    try:
        dom = parseString(stream(username, password, vcsrealm, vcs_buri, vcs_furi))
        xmlTag = dom.getElementsByTagName('Warnings')[0].toxml()
        # send email
        body = getalarmdetail(xmlTag)
        if body == '':
             break
        body_d = body[1]
        alarm_c = body[0]
        if str(alarm_c) > "1":
            subject = '[WARNING] ' + str(alarm_c) + ' unacknowledged alarms detected on ' + o[3]
        else:
            subject = '[WARNING] ' + str(alarm_c) + ' unacknowledged alarm detected on ' + o[3]
        msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n"
               % (fromadd, ", ".join(destadd), subject))
        msg = msg + body_d
        server = smtplib.SMTP(smtpsrv)
        server.sendmail(fromadd, [destadd], msg)
        server.quit()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print ( "Error: Basic authentication failed %s, please check your username and password" % e.code )
        elif e.code == 404:
            print ( "Error: Page not found %s, please check your configuration" % e.code )
        elif e.code == 408:
            print ( "Error: Request timed out %s" % e.code )
        else:
            print ( "Error: %s" % e.code )
    except urllib.error.URLError as e:
        print ( "Error opening URL: %s, please check your configuration" % e )
