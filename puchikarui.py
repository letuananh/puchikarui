#!/usr/bin/env python2
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
		self.template = collections.namedtuple(self.name, self.columns)

	def __str__(self):
		return "Table: %s - Columns: %s" % (self.name, self.columns) 

	def to_table(self, row_tuples):
		if not row_tuples:
			return None
		else:
			#return [ self.template(*x) for x in row_tuples if len(x) == len(self.columns) ]
			return [ self.template(*x) for x in row_tuples ]

	def to_row(self, row_tuple):
		return self.template(*row_tuple)

	def select(self, where=None, values=None, orderby=None, limit=None):
		if not self.data_source:
			return None
		else:
			query = "SELECT %s FROM %s " % (','.join(self.columns), self.name)
			if where:
				query += " WHERE " + where
			if orderby:
				query += " ORDER BY %s" % orderby
			if limit:
				query += " LIMIT %s" % limit
			result = self.data_source.execute(query, values)
		return self.to_table(result)

	def insert(self, values):
		if not self.data_source:
			return None
		else:
			query = "INSERT INTO %s (%s) VALUES (%s) " % (self.name, ','.join(self.columns), ','.join(['?']*len(self.columns)))
			try:
				result = self.data_source.execute(query, values)
				return result
			except Exception, e:
				print("Error: \n Query: %s \n Values: %s \n %s" % (query, values, e))
		
# Represent a database connection
class DataSource:
	  
	def __init__(self, filepath, auto_connect=True):
		self.filepath = filepath
		if auto_connect:
			self.open()

	def get_path(self):
		return self.filepath

	def open(self):
		self.conn = sqlite3.connect(self.get_path())
		self.cur = self.conn.cursor()
		self.conn.row_factory = sqlite3.Row

	def execute(self, query, params=None):
		# Try to connect to DB if not connected
		if not self.conn:
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

	def close(self):
		try:
			if self.conn:
				self.conn.close()
		except:
			print("Error while closing connection")

class Schema(object):
	def __init__(self, data_source=None):
		self.data_source = data_source
	  
	def add_table(self, name, columns):
		setattr(self, name, Table(name, columns, self.data_source))
		
	def ds(self):
		return self.data_source
	
	@classmethod
	def connect(cls, filepath):
		return cls(DataSource(filepath))
		
	def close(self):
		self.ds().close()

#-------------------------------------------------------------
# Schema definition
#-------------------------------------------------------------
#class SchemaDemo(Schema):
	#def define(self):
		#self.table('person', ['name', 'age'])

#-------------------------------------------------------------
# Main
#-------------------------------------------------------------
def main():
	print("PuchiKarui is a Python module, not an application")
	# s = SchemaDemo()

#-------------------------------------------------------------
if __name__ == "__main__":
	main()
