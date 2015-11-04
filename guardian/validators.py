#!/usr/bin/env python
import os
import socket
import subprocess
import argparse
import logging


LOGGER = logging.getLogger(__name__)


class ValidatorError(Exception):
    pass


def ping(address):
    try:
        subprocess.check_call(('ping', '-c 1', '-W 1', address), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        LOGGER.info('Ping server %s - OK', address)
    except subprocess.CalledProcessError as e:
        LOGGER.error('Ping server %s - Failed', address)
        raise ValidatorError(e)
ping.short_name = 'PING'


def port(address, port):
    s = socket.socket()
    try:
        s.connect((address, port))
        LOGGER.info('Checking port %s:%d - OK', address, port)
    except socket.error as e:
        LOGGER.error('Checking port %s:%d - Failed', address, port)
        raise ValidatorError(e)
port.short_name = 'PORT'
