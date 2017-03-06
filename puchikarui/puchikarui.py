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

#-------------------------------------------------------------
# PuchiKarui
# A minimalist SQLite wrapper library for Python which supports ORM features too.
#-------------------------------------------------------------


# A table schema
class Table:
    def __init__(self, name, columns, data_source=None):
        self.name = name
        self.columns = columns
        self.data_source = data_source

        try:
            collections.namedtuple(self.name, self.columns, verbose=False, rename=False)
        except Exception as ex:
            print("WARNING: Bad database design detected (Table: %s (%s)" % (name, columns))

        self.template = collections.namedtuple(self.name, self.columns, rename=True)

    def __str__(self):
        return "Table: %s - Columns: %s" % (self.name, self.columns)

    def to_table(self, row_tuples, columns=None):
        if not row_tuples:
            return None
        else:
            #return [ self.template(*x) for x in row_tuples if len(x) == len(self.columns) ]
            if columns:
                new_tuples = collections.namedtuple(self.name, columns, rename=True)
                return [new_tuples(*x) for x in row_tuples]
            else:
                return [self.template(*x) for x in row_tuples]

    def to_row(self, row_tuple):
        return self.template(*row_tuple)

    def select_single(self, where=None, values=None, orderby=None, limit=None, columns=None):
        ''' Select a single row
        '''
        result = self.select(where, values, orderby, limit, columns)
        if result and len(result) > 0:
            return result[0]
        else:
            return None

    def select(self, where=None, values=None, orderby=None, limit=None, columns=None):
        if not self.data_source:
            return None
        else:
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
            result = self.data_source.execute(query, values)
        return self.to_table(result, columns)

    def insert(self, values, columns=None):
        if not self.data_source:
            raise Exception("There is no available data source")
        else:
            if columns:
                column_names = ','.join(columns)
            elif len(values) < len(self.columns):
                column_names = ','.join(self.columns[-len(values):])
            else:
                column_names = ','.join(self.columns)
            query = "INSERT INTO %s (%s) VALUES (%s) " % (self.name, column_names, ','.join(['?'] * len(values)))
            try:
                result = self.data_source.execute(query, values)
                return result
            except Exception as e:
                logging.error("Error: \n DB: %s \n Query: %s \n Values: %s \n %s" % (self.data_source.filepath, query, values, e))

    def delete(self, where=None, values=None):
        if where:
            query = "DELETE FROM {tbl} WHERE {where}".format(tbl=self.name, where=where)
        else:
            query = "DELETE FROM {tbl}".format(tbl=self.name)
        try:
            logging.debug("Executing: {q} | values={v}".format(q=query, v=values))
            self.data_source.execute(query, values)
            self.data_source.commit()
            self.data_source.close()
        except Exception as e:
                logging.error("Error: \n DB: %s \n Query: %s \n Values: %s \n %s" % (self.data_source.filepath, query, values, e))
                raise e


# Represent a database connection
class DataSource:

    def __init__(self, filepath, setup_script=None, setup_file=None):
        self.filepath = filepath
        self.conn = None
        self.cur = None
        if setup_file is not None:
            with open(setup_file, 'r') as scriptfile:
                logging.debug("Setup script file provided: {}".format(setup_file))
                self.setup_file = scriptfile.read()
        else:
            self.setup_file = None
        self.setup_script = setup_script

    def get_path(self):
        return self.filepath

    def is_online(self):
        ''' Check if Data Source is serving '''
        try:
            if self.conn is not None:
                return self.execute("SELECT 1;").fetchone()[0]
        except Exception as e:
            # make sure to close DB connection in the end
            self.close()
        return False

    def open(self):
        try:
            self.conn = sqlite3.connect(self.get_path())
            self.cur = self.conn.cursor()
            self.conn.row_factory = sqlite3.Row
            if not os.path.isfile(self.get_path()) or os.path.getsize(self.get_path()) == 0:
                print("Need setup")
                # run setup script
                if self.setup_file is not None:
                    self.cur.executescript(self.setup_file)
                if self.setup_script is not None:
                    self.cur.executescript(self.setup_script)
                self.conn.commit()
        except Exception as e:
            logging.error("Error was raised while trying to connect to DB file: %s" % (self.get_path(),))
            logging.error(e)
            raise

    def commit(self):
        if self.conn:
            try:
                self.conn.commit()
            except Exception as e:
                logging.error("Cannot commit changes. e = %s" % e)
            finally:
                self.conn = None

    def execute(self, query, params=None):
        # Try to connect to DB if not connected
        if self.conn is None:
            self.open()
        if params:
            return self.cur.execute(query, params)
        else:
            return self.cur.execute(query)

    def executescript(self, query):
        # Try to connect to DB if not connected
        if self.conn is None:
            self.open()
        return self.cur.executescript(query)

    def executefile(self, file_loc):
        with open(file_loc, 'r') as script_file:
            script_text = script_file.read()
            self.executescript(script_text)

    def close(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except:
            logging.error("Error while closing connection")
        finally:
            self.conn = None


class Execution(object):
    ''' Create a context to work with a schema which closes connection when destroyed
    '''
    def __init__(self, schema):
        self.schema = schema

    def __enter__(self):
        self.ds = self.schema.ds()
        return self

    def __exit__(self, type, value, traceback):
        try:
            self.ds.close()
        except Exception as e:
            logging.error("Error was raised while closing DB connection. e = %s" % e)
        finally:
            self.ds = None


class Schema(object):
    ''' Contains schema definition of a database
    '''
    def __init__(self, data_source, setup_script=None, setup_file=None, auto_commit=True):
        if type(data_source) is DataSource:
            self.data_source = data_source
        else:
            self.data_source = DataSource(data_source, setup_script=setup_script, setup_file=setup_file)
        self.auto_commit = auto_commit

    def add_table(self, name, columns, alias=None):
        tbl_obj = Table(name, columns, self.data_source)
        setattr(self, name, tbl_obj)
        if alias:
            setattr(self, alias, tbl_obj)

    def ds(self):
        return self.data_source

    @classmethod
    def connect(cls, filepath):
        ''' [DEPRECATED] Connect to a database
        It's possible to pass a string directly into the constructor to create a Schema object
        so this method is no longer in used
        '''
        return cls(DataSource(filepath))

    def reconnect(self, silent=True):
        try:
            self.ds().close()
        except:
            if not silent:
                raise
        self.ds().open()

    def commit(self, silent=False):
        try:
            self.ds().commit()
        except:
            if not silent:
                raise

    def close(self):
        if self.auto_commit:
            self.ds().commit()
        self.ds().close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        try:
            # logging.error("Closing database ...")
            self.close()
        except Exception as e:
            # [TODO] Log exception properly
            logging.error("Error was raised while closing DB connection. e = %s" % e)


#-------------------------------------------------------------
# Main
#-------------------------------------------------------------

def main():
    print("PuchiKarui is a Python module, not an application")


#-------------------------------------------------------------
if __name__ == "__main__":
    main()
