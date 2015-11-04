#!/usr/bin/env python
import sqlite3
import datetime
import logging


LOGGER = logging.getLogger(__name__)


class WatchDb(object):
    def __init__(self, db_path='watch.db',keep=31):
        self.conn = sqlite3.connect(db_path)
        self.keep = keep
        self.cur = self.conn.cursor()
        if not self._table_exists('watch_log'):
            self._execute('''CREATE TABLE watch_log 
                             (created_at timestamp, server varchar(255), test varchar(255), args varchar(255), passed char(1))''')
        else:
            self.flush()

    def __del__(self):
        if self.conn:
            self.conn.close()

    def _execute(self, sql, args=tuple()):
        self.cur.execute(sql, args)
        data = self.cur.fetchall()
        self.conn.commit()
        return data

    def _table_exists(self, table_name):
        return bool(self._execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)))

    def flush(self):
        month_ago = datetime.datetime.now() - datetime.timedelta(days=self.keep)
        LOGGER.info("Flushing entries older than %s", month_ago)
        self._execute("DELETE FROM watch_log WHERE created_at < ?", (month_ago,))

    def add(self, server, test, args, passed):
        passed = '1' if passed else '0'
        args = ':'.join(str(i) for i in args)
        self._execute("INSERT INTO watch_log VALUES(?, ?, ?, ?, ?)", (datetime.datetime.now(), server, test, args, passed))      
    
    def get_latest(self, latest=60):
        timedelta = datetime.datetime.now() - datetime.timedelta(minutes=latest)
        sql = """
        SELECT
            server,
            test,
            args,
            (SELECT
                 created_at
             FROM 
                 watch_log 
             WHERE 
                 server=wl.server and test=wl.test and args=wl.args and passed = '1' and created_at > ?
             ORDER BY
                 created_at DESC 
             LIMIT 1) as last_passed_at,
            (SELECT
                 created_at
             FROM 
                 watch_log 
             WHERE 
                 server=wl.server and test=wl.test and args=wl.args and passed = '0' and created_at > ?
             ORDER BY
                 created_at DESC 
             LIMIT 1) as last_failed_at
        FROM 
            watch_log as wl
        GROUP BY
            server, test, args;
        """
        return self._execute(sql, (timedelta, timedelta))

    def get_status(self, latest=60):
        timedelta = datetime.datetime.now() - datetime.timedelta(minutes=latest)
        return not bool(self._execute("SELECT COUNT(*) FROM watch_log WHERE created_at > ? and passed = '0'", (timedelta,))[0][0])

