# -*- coding: utf-8 -*-

import os

from email.header import Header
from email.mime.text import MIMEText
from email.utils import formatdate
from smtplib import SMTP_SSL

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'env.py')
if os.path.exists(env_file):
    exec(open(env_file, 'rb').read())


class EmailClient(object):
    def __init__(self, user=None, password=None):
        self.user = user or LOGIN_USERNAME
        self.password = password or LOGIN_PASSWORD
        self.smtp_host = 'smtp.gmail.com'
        self.smtp_port = 465
        self.imap_host = 'imap.gmail.com'
        self.imap_port = 993
        self.email_default_encoding = 'utf-8'  # 'iso-2022-jp'
        self.timeout = 1 * 60  # sec

    def send_email(self, subject, body, from_address, to_addresses, cc_addresses=None, bcc_addresses=None):
        """
        Send an email

        Args:
            to_addresses: must be a list
            cc_addresses: must be a list
            bcc_addresses: must be a list
        """
        try:
            # Note: need Python 2.6.3 or more
            conn = SMTP_SSL(self.smtp_host, self.smtp_port)
            conn.login(self.user, self.password)
            msg = MIMEText(body, 'plain', self.email_default_encoding)
            msg['Subject'] = Header(subject, self.email_default_encoding)
            msg['From'] = from_address
            msg['To'] = ', '.join(to_addresses)
            if cc_addresses:
                msg['CC'] = ', '.join(cc_addresses)
            if bcc_addresses:
                msg['BCC'] = ', '.join(bcc_addresses)
            msg['Date'] = formatdate(localtime=True)
            conn.sendmail(from_address, to_addresses, msg.as_string())
        except:
            raise
        finally:
            conn.close()

    def send_test_email(self, subject, body):
        self.send_email(subject, body, self.user, [self.user])
