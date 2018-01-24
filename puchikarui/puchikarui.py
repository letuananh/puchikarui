# -*- coding: utf-8 -*-

'''
Minimalist SQLite ORM engine for Python

Latest version can be found at https://github.com/letuananh/puchikarui

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
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

########################################################################

import os
import sqlite3
import collections
import logging
import functools


# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------
# Functions
# -------------------------------------------------------------

# A table schema
class Table:
    def __init__(self, name, *columns, data_source=None, proto=None, id_cols=('rowid',), **field_map):
        self.name = name
        self.columns = []
        self.add_fields(*columns)
        self._data_source = data_source
        self._proto = proto
        self._id_cols = id_cols if id_cols else []
        self._field_map = field_map

    def add_fields(self, *columns):
        self.columns.extend(columns)
        try:
            collections.namedtuple(self.name, self.columns, verbose=False, rename=False)
        except Exception as ex:
            getLogger().warning("WARNING: Bad database design detected (Table: %s (%s)" % (self.name, self.columns))
        self.template = collections.namedtuple(self.name, self.columns, rename=True)
        return self

    @property
    def id_cols(self):
        return self._id_cols

    def set_id(self, *id_cols):
        self._id_cols.extend(id_cols)
        return self

    def set_proto(self, proto):
        self._proto = proto
        return self

    def field_map(self, **field_map):
        self._field_map.update(field_map)
        return self

    def __str__(self):
        return "Table: %s - Cols: %s" % (self.name, self.columns)

    def to_table(self, row_tuples, columns=None):
        if not row_tuples:
            raise ValueError("Invalid row_tuples")
        else:
            if self._proto:
                return [self.to_obj(x, columns) for x in row_tuples]
            if columns:
                new_tuples = collections.namedtuple(self.name, columns, rename=True)
                return [self.to_row(x, new_tuples) for x in row_tuples]
            else:
                return [self.to_row(x) for x in row_tuples]

    def to_row(self, row_tuple, template=None):
        if template:
            return template(*row_tuple)
        else:
            return self.template(*row_tuple)

    def to_obj(self, row_tuple, columns=None):
        # fall back to row_tuple
        if not self._proto:
            return self.to_row(row_tuple)
        # else create objects
        if not columns:
            columns = self.columns
        new_obj = to_obj(self._proto, dict(zip(columns, row_tuple)), *columns, **self._field_map)
        # assign values
        return new_obj

    def select_single(self, where=None, values=None, orderby=None, limit=None, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).select_single(where=where, values=values, orderby=orderby, limit=limit, columns=columns)
        else:
            with self._data_source.open() as ctx:
                return self.ctx(ctx).select_single(where=where, values=values, orderby=orderby, limit=limit, columns=columns)

    def select(self, where=None, values=None, orderby=None, limit=None, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).select(where, values, orderby=orderby, limit=limit, columns=columns)
        else:
            with self._data_source.open() as ctx:
                return self.ctx(ctx).select(where, values, orderby=orderby, limit=limit, columns=columns)

    def ctx(self, ctx):
        return TableContext(self, ctx)

    def insert(self, *values, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).insert(*values, columns=columns)
        else:
            with self._data_source.open() as ctx:
                return self.ctx(ctx).insert(*values, columns=columns)

    def delete(self, where=None, values=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).delete(where=where, values=values)
        else:
            with self._data_source.open() as ctx:
                return self.ctx(ctx).delete(where=where, values=values)

    def delete_obj(self, obj, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).delete_obj(obj)
        else:
            with self._data_source.open() as ctx:
                return self.ctx(ctx).delete_obj()

    def update(self, new_values, where='', where_values=None, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).update(new_values, where, where_values, columns)
        else:
            with self._data_source.open() as ctx:
                return self.ctx(ctx).update(new_values, where, where_values, columns)

    def by_id(self, *args, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).by_id(*args, columns=columns)
        else:
            with self._data_source.open() as ctx:
                return self.ctx(ctx).by_id(*args, columns=columns)

    def save(self, obj, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).save(obj, columns)
        else:
            with self._data_source.open() as ctx:
                return self.ctx(ctx).save(obj, columns)


class DataSource:

    def __init__(self, db_path, schema=None):
        self._filepath = db_path
        self._script_file_map = {}
        self.schema = schema

    @property
    def path(self):
        return self._filepath

    def read_file(self, path):
        if path not in self._script_file_map:
            with open(path, 'r') as script_file:
                self._script_file_map[path] = script_file.read()
        return self._script_file_map[path]

    def open(self, auto_commit=None, schema=None):
        ''' Create a context to execute queries '''
        if schema is None:
            schema = self.schema
        ac = auto_commit if auto_commit is not None else schema.auto_commit
        exe = ExecutionContext(self.path, schema=schema, auto_commit=ac)
        # setup DB if required
        if not os.path.isfile(self.path) or os.path.getsize(self.path) == 0:
            getLogger().warning("DB does not exist. Setup is required.")
            # run setup files
            if schema is not None and schema.setup_files:
                for file_path in schema.setup_files:
                    getLogger().debug("Executing script file: {}".format(file_path))
                    exe.cur.executescript(self.read_file(file_path))
            # run setup scripts
            if schema.setup_scripts:
                for script in schema.setup_scripts:
                    exe.cur.executescript(script)
        return exe

    def select(self, query, params=None):
        with self.open() as exe:
            return exe.select(query, params)

    def select_single(self, query, params=None):
        with self.open() as exe:
            return exe.select_single(query, params)

    def select_scalar(self, query, params=None):
        with self.open() as exe:
            return exe.select_scalar(query, params)

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


def update_obj(source, target, *fields, **field_map):
    source_dict = source.__dict__ if hasattr(source, '__dict__') else source
    if not fields:
        fields = source_dict.keys()
    for f in fields:
        target_f = f if f not in field_map else field_map[f]
        setattr(target, target_f, source_dict[f])


def to_obj(cls, obj_data=None, *fields, **field_map):
    ''' prioritize obj_dict when there are conficts '''
    obj_dict = obj_data.__dict__ if hasattr(obj_data, '__dict__') else obj_data
    if not fields:
        fields = obj_dict.keys()
    obj = cls()
    update_obj(obj_dict, obj, *fields, **field_map)
    return obj


class QueryBuilder(object):

    ''' Default query builder '''
    def __init__(self, schema):
        self.schema = schema

    def build_select(self, table, where=None, orderby=None, limit=None, columns=None):
        query = []
        if not columns:
            columns = table.columns
        query.append("SELECT ")
        query.append(','.join(columns))
        query.append(" FROM ")
        query.append(table.name)
        if where:
            query.append(" WHERE ")
            query.append(where)
        if orderby:
            query.append(" ORDER BY ")
            query.append(orderby)
        if limit:
            query.append(" LIMIT ")
            query.append(str(limit))
        return ''.join(query)

    def build_insert(self, table, values, columns=None):
        ''' Insert an active record into DB and return lastrowid if available '''
        if not columns:
            columns = table.columns
        if len(values) < len(columns):
            column_names = ','.join(columns[-len(values):])
        else:
            column_names = ','.join(columns)
        query = "INSERT INTO %s (%s) VALUES (%s) " % (table.name, column_names, ','.join(['?'] * len(values)))
        return query

    def build_update(self, table, where='', columns=None):
        if columns is None:
            columns = table.columns
        set_fields = []
        for col in columns:
            set_fields.append("{c}=?".format(c=col))
        if where:
            query = 'UPDATE {t} SET {sf} WHERE {where}'.format(t=table.name, sf=', '.join(set_fields), where=where)
        else:
            query = 'UPDATE {t} SET {sf}'.format(t=table.name, sf=', '.join(set_fields))
        return query

    def build_delete(self, table, where=None):
        if where:
            query = "DELETE FROM {tbl} WHERE {where}".format(tbl=table.name, where=where)
        else:
            query = "DELETE FROM {tbl}".format(tbl=self.name)
        return query


class TableContext(object):
    def __init__(self, table, context):
        self._table = table
        self._context = context

    def select(self, where=None, values=None, **kwargs):
        return self._context.select_record(self._table, where, values, **kwargs)

    def select_single(self, where=None, values=None, **kwargs):
        result = self._context.select_record(self._table, where, values, **kwargs)
        if result and len(result) > 0:
            return result[0]
        else:
            return None

    def insert(self, *values, columns=None):
        return self._context.insert_record(self._table, values, columns)

    def update(self, new_values, where='', where_values=None, columns=None):
        return self._context.update_record(self._table, new_values, where, where_values, columns)

    def delete(self, where=None, values=None):
        return self._context.delete_record(self._table, where, values)

    def by_id(self, *args, columns=None):
        return self._context.select_object_by_id(self._table, args, columns)

    def save(self, obj, columns=None):
        existed = True and len(self._table.id_cols) > 0
        for i in self._table.id_cols:
            existed = existed and getattr(obj, i)
        if existed:
            # update
            return self._context.update_object(self._table, obj, columns, self._table._field_map)
        else:
            # insert
            return self._context.insert_object(self._table, obj, columns, self._table._field_map)

    def delete_obj(self, obj):
        return self._context.delete_object(self._table, obj)


class ExecutionContext(object):
    ''' Create a context to work with a schema which closes connection when destroyed
    '''
    def __init__(self, path, schema, auto_commit=True):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.schema = schema
        self.auto_commit = auto_commit

    def buckmode(self):
        self.cur.execute("PRAGMA cache_size=80000000")
        self.cur.execute("PRAGMA journal_mode=MEMORY")
        self.cur.execute("PRAGMA temp_store=MEMORY")
        # self.cur.execute("PRAGMA count_changes=OFF")
        return self

    def commit(self):
        if self.conn:
            try:
                self.conn.commit()
            except Exception as e:
                getLogger().exception("Cannot commit changes. e = %s" % e)

    def select_record(self, table, where=None, values=None, orderby=None, limit=None, columns=None):
        ''' Support these keywords where, values, orderby, limit and columns'''
        query = self.schema.query_builder.build_select(table, where, orderby, limit, columns)
        return table.to_table(self.execute(query, values), columns=columns)

    def insert_record(self, table, values, columns=None):
        query = self.schema.query_builder.build_insert(table, values, columns)
        self.execute(query, values)
        return self.cur.lastrowid

    def update_record(self, table, new_values, where='', where_values=None, columns=None):
        query = self.schema.query_builder.build_update(table, where, columns)
        return self.execute(query, new_values + where_values if where_values else new_values)

    def delete_record(self, table, where=None, values=None):
        query = self.schema.query_builder.build_delete(table, where)
        getLogger().debug("Executing: {q} | values={v}".format(q=query, v=values))
        return self.execute(query, values)

    def select_object_by_id(self, table, ids, columns=None):
        where = ' AND '.join(['{c}=?'.format(c=c) for c in table._id_cols])
        results = self.select_record(table, where, ids, columns=columns)
        if results:
            return results[0]
        else:
            return None

    def insert_object(self, table, obj_data, columns=None, field_map=None):
        if not columns:
            columns = table.columns
        values = tuple(getattr(obj_data, field_map[colname] if field_map and colname in field_map else colname) for colname in columns)
        self.insert_record(table, values, columns)
        return self.cur.lastrowid

    def update_object(self, table, obj_data, columns=None, field_map=None):
        where = ' AND '.join(['{c}=?'.format(c=c) for c in table._id_cols])
        where_values = tuple(getattr(obj_data, colname) for colname in table._id_cols)
        if not columns:
            columns = table.columns
        new_values = tuple(getattr(obj_data, field_map[colname] if field_map and colname in field_map else colname) for colname in columns)
        self.update_record(table, new_values, where, where_values, columns)

    def delete_object(self, table, obj_data):
        where = ' AND '.join(['{c}=?'.format(c=c) for c in table._id_cols])
        where_values = tuple(getattr(obj_data, colname) for colname in table._id_cols)
        self.delete_record(table, where, where_values)

    def select(self, query, params=None):
        return self.execute(query, params).fetchall()

    def select_single(self, query, params=None):
        return self.execute(query, params).fetchone()

    def select_scalar(self, query, params=None):
        return self.select_single(query, params)[0]

    def execute(self, query, params=None):
        # Try to connect to DB if not connected
        try:
            getLogger().debug('Executing q={} | p={}'.format(query, params))
            if params:
                return self.cur.execute(query, params)
            else:
                return self.cur.execute(query)
        except:
            getLogger().exception('Invalid query. q={}, p={}'.format(query, params))
            raise

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
            getLogger().exception("Error while closing connection")
        finally:
            self.conn = None

    def __getattr__(self, name):
        if not self.schema or name not in self.schema._tables:
            raise AttributeError('Attribute {} does not exist'.format(name))
        else:
            tbl = getattr(self.schema, name)
            ctx = TableContext(tbl, self)
            setattr(self, name, ctx)
            return getattr(self, name)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        try:
            self.close()
        except Exception as e:
            getLogger().exception("Error was raised while closing DB connection. e = %s" % e)


class Schema(object):
    ''' Contains schema definition of a database
    '''
    def __init__(self, data_source, setup_script=None, setup_file=None, auto_commit=True):
        if type(data_source) is DataSource:
            self.data_source = data_source
        else:
            self.data_source = DataSource(data_source, schema=self)
        self.auto_commit = auto_commit
        self.setup_files = []
        if setup_file:
            self.setup_files.append(setup_file)
        self.setup_scripts = []
        if setup_script:
            self.setup_scripts.append(setup_script)
        self._tables = {}
        self.query_builder = QueryBuilder(self)

    def add_file(self, setup_file):
        self.setup_files.append(setup_file)
        return self

    def add_script(self, setup_script):
        self.setup_scripts.append(setup_script)
        return self

    def add_table(self, name, columns=None, proto=None, id_cols=None, alias=None, **field_map):
        if not columns:
            columns = []
        tbl_obj = Table(name, *columns, data_source=self.data_source, proto=proto, id_cols=id_cols, **field_map)
        setattr(self, name, tbl_obj)
        self._tables[name] = tbl_obj
        if alias:
            setattr(self, alias, tbl_obj)
            self._tables[alias] = tbl_obj
        return tbl_obj

    @property
    def ds(self):
        return self.data_source

    def ctx(self):
        ''' Create a new execution context '''
        return self.ds.open(schema=self)


def with_ctx(func=None):
    ''' Auto create a new context if not available '''
    if not func:
        return functools.partial(with_ctx)

    @functools.wraps(func)
    def func_with_context(_obj, *args, **kwargs):
        if 'ctx' not in kwargs or kwargs['ctx'] is None:
            # if context is empty, ensure context
            with _obj.ctx() as new_ctx:
                kwargs['ctx'] = new_ctx
                return func(_obj, *args, **kwargs)
        else:
            # if context is available, just call the function
            return func(_obj, *args, **kwargs)

    return func_with_context
