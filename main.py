#!/usr/bin/env python
import os
import sys
import json
import subprocess
import argparse
import logging

from mailer import Mailer, Message
from jinja2 import Environment, FileSystemLoader

import validators
import database


LOGGER = logging.getLogger('watch')
CONFIG_TEMPLATE = {
    "smtp": {
        "host": "smtp.example.com",
        "port": 587,
        "user": "user@example.com",
        "password": "secret"
    },
    "notify": {
        "subject": "Failure!",
        "email": "admin@example.com",
        "track_last": 60
    },
    "servers": [
        {
            "name": "localhost",
            "address": "127.0.0.1",
            "ports": [80, 22]
        },
    ]
}

def loglevel(value):
    try:
        return getattr(logging, value.upper())
    except AttributeError:
        raise argparse.ArgumentTypeError("Invalid loglevel.")


def stats(args, config, db):
    LOGGER.info("Getting server stats...")
    for server in config['servers']:
        LOGGER.info("Checking %s", server['name'])
        args = (server['address'],)
        try:
            validators.ping(*args)
            db.add(server['name'], validators.ping.short_name, args, True)
        except validators.ValidatorError as e:
            db.add(server['name'], validators.ping.short_name, args, False)
        for port in server['ports']:
            args = server['address'], port
            try:
                validators.port(*args)
                db.add(server['name'], validators.port.short_name, args, True)
            except validators.ValidatorError as e:
                db.add(server['name'], validators.port.short_name, args, False)


def notify(args, config, db):
    LOGGER.info("Notify if something is not working...")
    
    if db.get_status(config['notify']['track_last']):
        LOGGER.info("Everything seems to be ok.")
    else:
        LOGGER.warning("One of tests failed, generate report.")
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('template.html')
        body = template.render(table=db.get_latest(config['notify']['track_last']))
        LOGGER.info("Sending email...")
        sender = Mailer(
            config['smtp']['host'],
            port=config['smtp']['port'],
            usr=config['smtp']['user'],
            pwd=config['smtp']['password'],
        )
        message = Message(
            From=config['smtp']['user'],
            To=config['notify']['email'],
        )
        message.Subject = config['notify']['subject']
        message.Html = body
        sender.send(message)

def main():
    parser = argparse.ArgumentParser(__doc__)
    subparsers = parser.add_subparsers(title='subcommands')
    subparser_notify = subparsers.add_parser('notify', help="Send email if one of servers is inactive.")
    subparser_notify.set_defaults(func=notify)

    subparser_stats = subparsers.add_parser('stats', help="Gather statistics and save them in database.")
    subparser_stats.set_defaults(func=stats)

    parser.add_argument('-c', '--config', default='~/.watcher/config.json', help='Path to config file')
    parser.add_argument('-l', '--log', default=logging.INFO,
                        type=loglevel,
                        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                        help='Logging level')
    args = parser.parse_args()

    # Set up logger
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=args.log
    )

    config_path = os.path.abspath(os.path.expanduser(args.config))
    LOGGER.info("Parsing config file: %s", config_path)
    try:
        with open(config_path) as f:
            config = json.loads(f.read())
    except IOError:
        LOGGER.error("File {} does not exists.".format(config_path))
        LOGGER.info("Creating new config file...")
        os.makedirs(os.path.dirname(config_path))
        with open(config_path, 'w') as f:
            f.write(json.dumps(CONFIG_TEMPLATE))
        sys.exit(1)

    db = database.WatchDb(db_path=os.path.expanduser('~/.watcher/watch.db'))

    # Execute subcommand function
    args.func(args, config, db)


if __name__ == '__main__':
    main()  
