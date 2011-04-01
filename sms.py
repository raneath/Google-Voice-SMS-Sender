#!/usr/bin/env python
"""Google Voice SMS Sender
usage:  sms.py RECIPIENT

  -h, --help      Usage information
  RECIPIENT       Name that SMS will be sent to
"""
import getopt
import getpass
import httplib
import json
import re
import sys
import urllib

DEBUG = False

class GVSms:

    APP_NAME = 'raneath-gvsms-0.1'

    def __init__(self, recipient):
        self.recipient = recipient
        self.get_contacts()
        self.get_recipient()
        self.get_auth()
        self.get_rnrse()
        self.get_message()
        self.send_sms()

    def get_contacts(self):
        self.contacts = json.load(open("addressbook.json"))

    def get_recipient(self):
        recipient = self.recipient.lower()
        if recipient in self.contacts:
            self.recipient_number = self.contacts[self.recipient.lower()]
        else:
            raise RecipientNotFound("Unable to find \"%s\" in address book" % recipient)

    def get_auth(self):
        HOST_CLIENTLOGIN = "www.google.com:443"
        PATH_CLIENTLOGIN = "/accounts/ClientLogin"
        POST_CLIENTLOGIN = "accountType=GOOGLE&Email=%s&Passwd=%s&service=grandcentral&source=%s"

        data = ""
        if DEBUG:
            data = open("debug_auth", 'r').read()
        else:
            sys.stdout.write("Gmail Account: ")
            email = urllib.quote_plus(sys.stdin.readline().rstrip())
            password = urllib.quote_plus(getpass.getpass('Password: '))
            params = POST_CLIENTLOGIN % (email, password, self.APP_NAME)
            headers = { "Content-type": "application/x-www-form-urlencoded" }

            conn = httplib.HTTPSConnection(HOST_CLIENTLOGIN)
            conn.request("POST", PATH_CLIENTLOGIN, params, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()

            """
            f = open("debug_auth", "w")
            f.write(data)
            f.close()
            """

        lines = data.split("\n")
        auth_items = dict([(line.split("=")[0], line.split("=")[1]) for line in lines if len(line.split("=")) > 1])
        self.auth = auth_items['Auth']

    def get_rnrse(self):
        HOST_RNRSE = "www.google.com:443"
        PATH_RNRSE = "/voice"

        data = ""
        if DEBUG:
            data = open("debug_rnrse", "r").read()
        else:
            headers = { "Authorization": "GoogleLogin auth=%s" % self.auth }
            conn = httplib.HTTPSConnection(HOST_RNRSE)
            conn.request("GET", PATH_RNRSE, None, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()

            """
            f = open("debug_rnrse", "w")
            f.write(data)
            f.close()
            """

        m = re.search(r'<input name="_rnr_se" type="hidden" value="(.+?)"/>', data)
        if m is not None:
            self.rnrse = m.group(1)

    def get_message(self):
        sys.stdout.write("SMS message: ")
        self.message = urllib.quote_plus(sys.stdin.readline().rstrip())

    def send_sms(self):
        if self.rnrse is not None:
            HOST_SENDSMS = "www.google.com:443"
            PATH_SENDSMS = "/voice/sms/send/"
            POST_SENDSMS = "id=&phoneNumber=%s&text=%s&_rnr_se=%s"

            if not DEBUG:
                params = POST_SENDSMS % (self.recipient_number, self.message, self.rnrse)
                headers = { "Content-type":     "application/x-www-form-urlencoded",
                            "Authorization":   "GoogleLogin auth=%s" % self.auth  }
   
                conn = httplib.HTTPSConnection(HOST_SENDSMS)
                conn.request("POST", PATH_SENDSMS, params, headers)
                response = conn.getresponse()
                data = response.read()
                conn.close()

            print "Sent!"
        else:
            print "SMS could not be sent!"

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

class RecipientNotFound(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
        except getopt.error, msg:
             raise Usage(msg)

        recipient = None
        for o, a in opts:
            if o in ("-h", "--help"):
                print __doc__
                return 0

        if len(argv) < 2:
            print __doc__
            return 0

        recipient = argv[-1]
        GVSms(recipient)
        return 0

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2
    except RecipientNotFound, err:
        print >>sys.stderr, err.msg
        return 2

if __name__ == "__main__":
    sys.exit(main())
