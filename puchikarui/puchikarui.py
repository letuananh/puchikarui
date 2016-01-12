#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import sys
import codecs
import sqlite3
import os
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
                return [ new_tuples(*x) for x in row_tuples ]
            else:
                return [ self.template(*x) for x in row_tuples ]

    def to_row(self, row_tuple):
        return self.template(*row_tuple)

    def select_single(self, where=None, values=None, orderby=None, limit=None,columns=None):
        ''' Select a single row
        '''
        result = self.select(where, values, orderby, limit, columns)
        if result and len(result) > 0:
            return result[0]
        else:
            return None

    def select(self, where=None, values=None, orderby=None, limit=None,columns=None):
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

    def insert(self, values):
        if not self.data_source:
            return None
        else:
            query = "INSERT INTO %s (%s) VALUES (%s) " % (self.name, ','.join(self.columns), ','.join(['?']*len(self.columns)))
            try:
                result = self.data_source.execute(query, values)
                return result
            except Exception as e:
                logging.error("Error: \n Query: %s \n Values: %s \n %s" % (query, values, e))
        
# Represent a database connection
class DataSource:
      
    def __init__(self, filepath, auto_connect=True):
        self.filepath = filepath
        if auto_connect:
            self.open()

    def get_path(self):
        return self.filepath

    def open(self):
        try:
            self.conn = sqlite3.connect(self.get_path())
            self.cur = self.conn.cursor()
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            logging.error("ErrorError was raised while trying to connect to DB file: %s" % (self.get_path(),))
            logging.error(e)
            raise

    def commit(self):
        if self.conn:
            try:
                self.conn.commit()
            except Exception as e:
                logging.error("Cannot commit changes. e = %s" % e)
    
    def execute(self, query, params=None):
        # Try to connect to DB if not connected
        if (not self.conn):
            self.open()
        if params: 
            return self.cur.execute(query, params)
        else:
            return self.cur.execute(query)

    def executescript(self, query):
        # Try to connect to DB if not connected
        if not self.conn:
            self.open()
        return self.cur.executescript(query)
        
    def executefile(self, file_loc):
        with open(file_loc, 'r') as script_file:
            script_text = script_file.read()
            self.executescript(script_text)

    def close(self):
        try:
            if self.conn:
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
            loggin.error("Error was raised while closing DB connection. e = %s" % e)
        finally:
            self.ds = None

class Schema(object):
    ''' Contains schema definition of a database
    '''
    def __init__(self, data_source=None):
        if type(data_source) is DataSource:
            self.data_source = data_source
        else:
            self.data_source = DataSource(data_source)
      
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
    
    def close(self):
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
