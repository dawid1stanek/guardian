#!/usr/bin/env python
import os
import sys
import json
import subprocess
import argparse
import logging

from pkg_resources import resource_string
from mailer import Mailer, Message
from jinja2 import Environment, FileSystemLoader

import validators
import database


LOGGER = logging.getLogger('watch')
DIRECTORY = os.path.expanduser('~/.guardian/')
DB_PATH = os.path.join(DIRECTORY, 'watch.db')
CONFIG_PATH = os.path.join(DIRECTORY, 'config.json')


def loglevel(value):
    try:
        return getattr(logging, value.upper())
    except AttributeError:
        raise argparse.ArgumentTypeError("Invalid loglevel.")


def parse_config(config_path):
    LOGGER.info("Parsing config file: %s", config_path)
    try:
        with open(config_path) as f:
            return json.loads(f.read())
    except IOError:
        LOGGER.error("File {0} does not exists.".format(config_path))
        sys.exit(1)


def install(*args):
    LOGGER.info("Installing template files in {0} directory.".format(DIRECTORY))
    try:
        os.mkdir(DIRECTORY)
    except OSError:
        LOGGER.error('{0} already exists, please remove it manually'.format(DIRECTORY))
        return
    with open(os.path.join(DIRECTORY, 'config.json'), 'w') as f:
        f.write(resource_string(__name__, 'data/config.json'))
    with open(os.path.join(DIRECTORY, 'template.html'), 'w') as f:
        f.write(resource_string(__name__, 'data/template.html'))
        

def stats(args):
    config = parse_config(args.config)
    db = database.WatchDb(db_path=DB_PATH)
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


def notify(args):
    config = parse_config(args.config)  
    db = database.WatchDb(db_path=DB_PATH)
    LOGGER.info("Notify if something is not working...")
    if db.get_status(config['notify']['track_last']):
        LOGGER.info("Everything seems to be ok.")
    else:
        LOGGER.warning("One of tests failed, generate report.")
        env = Environment(loader=FileSystemLoader(DIRECTORY))
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

    subparser_install = subparsers.add_parser('install', help="Install template files in home directory.")
    subparser_install.set_defaults(func=install)

    parser.add_argument('-c', '--config', default=CONFIG_PATH, help='Path to config file')
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

    # Execute subcommand function
    args.func(args)


if __name__ == '__main__':
    main()  
