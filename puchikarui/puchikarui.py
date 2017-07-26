#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Mini SQLite ORM engine
Latest version can be found at https://github.com/letuananh/puchikarui

References:
    Python documentation:
        https://docs.python.org/
    Python unittest
        https://docs.python.org/3/library/unittest.html
    --
    argparse module:
        https://docs.python.org/3/howto/argparse.html
    PEP 257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''


# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2017, puchikarui"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

#-------------------------------------------------------------

import os
import sqlite3
import collections
import logging

#-------------------------------------------------------------
# CONFIGURATION
#-------------------------------------------------------------

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

#-------------------------------------------------------------
# PuchiKarui
# A minimalist SQLite wrapper library for Python which supports ORM features too.
#-------------------------------------------------------------


# A table schema
class Table:
    def __init__(self, name, columns, data_source=None):
        self.name = name
        self.columns = columns
        self._data_source = data_source
        try:
            collections.namedtuple(self.name, self.columns, verbose=False, rename=False)
        except Exception as ex:
            print("WARNING: Bad database design detected (Table: %s (%s)" % (name, columns))
        self.template = collections.namedtuple(self.name, self.columns, rename=True)

    def __str__(self):
        return "Table: %s - Cols: %s" % (self.name, self.columns)

    def to_table(self, row_tuples, columns=None):
        if not row_tuples:
            return None
        else:
            if columns:
                new_tuples = collections.namedtuple(self.name, columns, rename=True)
                return [new_tuples(*x) for x in row_tuples]
            else:
                return [self.template(*x) for x in row_tuples]

    def to_row(self, row_tuple):
        return self.template(*row_tuple)

    def select_single(self, where=None, values=None, orderby=None, limit=None, columns=None, exe=None):
        ''' Select a single row
        '''
        result = self.select(where, values, orderby, limit, columns, exe)
        if result and len(result) > 0:
            return result[0]
        else:
            return None

    def select(self, where=None, values=None, orderby=None, limit=None, columns=None, exe=None):
        if columns is not None:
            query = "SELECT %s FROM %s " % (','.join(columns), self.name)
        else:
            query = "SELECT %s FROM %s " % (','.join(self.columns), self.name)
        if where:
            query += " WHERE " + where
        if orderby:
            query += " ORDER BY %s" % orderby
        if limit:
            query += " LIMIT %s" % limit
        if exe is not None:
            return self.to_table(exe.execute(query, values))
        else:
            with self._data_source.open() as exe:
                result = exe.execute(query, values)
                return self.to_table(result, columns)

    def insert(self, values, columns=None, exe=None):
        ''' Insert an active record into DB and return lastrowid if available '''
        if columns:
            column_names = ','.join(columns)
        elif len(values) < len(self.columns):
            column_names = ','.join(self.columns[-len(values):])
        else:
            column_names = ','.join(self.columns)
        query = "INSERT INTO %s (%s) VALUES (%s) " % (self.name, column_names, ','.join(['?'] * len(values)))
        if exe is not None:
            exe.execute(query, values)
            return exe.cur.lastrowid
        else:
            with self._data_source.open() as exe:
                exe.execute(query, values)
                return exe.cur.lastrowid

    def delete(self, where=None, values=None, exe=None):
        if where:
            query = "DELETE FROM {tbl} WHERE {where}".format(tbl=self.name, where=where)
        else:
            query = "DELETE FROM {tbl}".format(tbl=self.name)
        logger.debug("Executing: {q} | values={v}".format(q=query, v=values))

        if exe is not None:
            exe.execute(query, values)
        else:
            with self._data_source.open() as exe:
                exe.execute(query, values)


class DataSource:

    def __init__(self, db_path, setup_script=None, setup_file=None, auto_commit=True):
        self._filepath = db_path
        self._setup_script = setup_script
        self.auto_commit = auto_commit
        if setup_file is not None:
            with open(setup_file, 'r') as scriptfile:
                logger.debug("Setup script file provided: {}".format(setup_file))
                self._setup_file = scriptfile.read()
        else:
            self._setup_file = None

    @property
    def path(self):
        return self._filepath

    def open(self, schema=None, auto_commit=None):
        ''' Create a context to execute queries '''
        ac = auto_commit if auto_commit is not None else self.auto_commit
        exe = ExecutionContext(self.path, schema=schema, auto_commit=ac)
        # setup DB if required
        if not os.path.isfile(self.path) or os.path.getsize(self.path) == 0:
            logger.warning("DB does not exist. Setup is required.")
            # run setup script
            if self._setup_file is not None:
                exe.cur.executescript(self._setup_file)
            if self._setup_script is not None:
                exe.cur.executescript(self._setup_script)
        return exe

    # Helper functions
    def execute(self, query, params=None):
        with self.open() as exe:
            return exe.execute(query, params)

    def executescript(self, query):
        with self.open() as exe:
            return exe.executescript(query)

    def executefile(self, file_loc):
        with self.open() as exe:
            return exe.executefile(file_loc)


class ExecutionContext(object):
    ''' Create a context to work with a schema which closes connection when destroyed
    '''
    def __init__(self, path, schema, auto_commit=True):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.schema = schema
        self.auto_commit = auto_commit

    def commit(self):
        if self.conn:
            try:
                self.conn.commit()
            except Exception as e:
                logging.exception("Cannot commit changes. e = %s" % e)

    def execute(self, query, params=None):
        # Try to connect to DB if not connected
        if params:
            return self.cur.execute(query, params)
        else:
            return self.cur.execute(query)

    def executescript(self, query):
        return self.cur.executescript(query)

    def executefile(self, file_loc):
        with open(file_loc, 'r') as script_file:
            script_text = script_file.read()
            self.executescript(script_text)

    def close(self):
        try:
            if self.conn is not None:
                if self.auto_commit:
                    self.commit()
                self.conn.close()
        except:
            logging.exception("Error while closing connection")
        finally:
            self.conn = None

    def __getattr__(self, name):
        if not self.schema or name not in self.schema._tables:
            raise AttributeError('Attribute {} does not exist'.format(name))
        else:
            return self.schema.table

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        try:
            self.close()
        except Exception as e:
            logger.exception("Error was raised while closing DB connection. e = %s" % e)


class Schema(object):
    ''' Contains schema definition of a database
    '''
    def __init__(self, data_source, setup_script=None, setup_file=None, auto_commit=True):
        if type(data_source) is DataSource:
            self.data_source = data_source
        else:
            self.data_source = DataSource(data_source, setup_script=setup_script, setup_file=setup_file, auto_commit=auto_commit)
        self.auto_commit = auto_commit
        self._tables = {}

    def add_table(self, name, columns, alias=None):
        tbl_obj = Table(name, columns, self.data_source)
        setattr(self, name, tbl_obj)
        self._tables[name] = tbl_obj
        if alias:
            setattr(self, alias, tbl_obj)
            self._tables[alias] = tbl_obj

    @property
    def ds(self):
        return self.data_source

    def exe(self):
        return self.ds.open(schema=self)


#-------------------------------------------------------------
# Main
#-------------------------------------------------------------

def main():
    print("PuchiKarui is a Python module, not an application")


#-------------------------------------------------------------
if __name__ == "__main__":
    main()
