#!/usr/bin/env python
import argparse
import smtplib
import json

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send(host, port, user, password, from_email, to_email, subject, message):
    server = smtplib.SMTP(host, port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(user, password)

    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = from_email
    message['To'] = to_email
    message.attach(MIMEText(message, 'html'))

    server.sendmail(from_email, to_email, message.as_string())
    server.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('-c', '--config', default='config.json', help="Config file")
    parser.add_argument('-r', '--recipient', help="Recipient")
    parser.add_argument('-s', '--subject', help="Subject")
    parser.add_argument('-m', '--message', help="Message")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.loads(f.read()) 

    send(
        config['smtp']['host'],
        config['smtp']['port'],
        config['smtp']['user'],
        config['smtp']['password'],
        config['smtp']['user'],
        args.recipient,
        args.subject,
        args.message,
    )
