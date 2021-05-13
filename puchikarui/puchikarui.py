# -*- coding: utf-8 -*-

''' A minimalist SQLite helper library for Python with ORM-like features
'''

# Latest version can be found at https://github.com/letuananh/puchikarui
# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>
# license: MIT

########################################################################

import os
import sqlite3
import collections
import logging
import functools


# -------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------

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


def escape_like(input_string, escape_char='@'):
    tranmap = {'%': escape_char + '%',
               '_': escape_char + '_',
               escape_char: escape_char + escape_char}
    new_str = []
    for c in input_string:
        if c in tranmap:
            new_str.append(tranmap[c])
        else:
            new_str.append(c)
    return ''.join(new_str)


def head_like(input_string, **kwargs):
    return escape_like(input_string, **kwargs) + '%'


def tail_like(input_string, **kwargs):
    return '%' + escape_like(input_string, **kwargs)


def contain_like(input_string, **kwargs):
    return '%' + escape_like(input_string, **kwargs) + '%'


# -------------------------------------------------------------
# Classes
# -------------------------------------------------------------

# A table schema
class Table:
    def __init__(self, name, *columns, data_source=None, proto=None, id_cols=('rowid',), strict_mode=False, **field_map):
        ''' Contains information of a table in the database
            strict_mode -- Warn users if a bad database design is detected (defaulted to False)
        '''
        self._strict_mode = strict_mode
        self.name = name
        self.columns = []
        self.add_fields(*columns)
        self._data_source = data_source
        self._proto = proto
        self._id_cols = id_cols if id_cols else []
        self._field_map = field_map

    def add_fields(self, *columns):
        self.columns.extend(columns)
        if self._strict_mode:
            try:
                collections.namedtuple(self.name, self.columns, rename=False)
            except Exception as ex:
                logging.getLogger(__name__).warning("WARNING: Bad database design detected (Table: %s (%s)" % (self.name, self.columns))
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

    def __repr__(self):
        return f"Table({repr(self.name)}, *{repr(self.columns)})"

    def __str__(self):
        return repr(self)

    def to_table(self, row_tuples, columns=None):
        return [self.to_obj(x, columns) for x in row_tuples]

    def to_row(self, row_tuple, template=None):
        if template:
            return template(*row_tuple)
        else:
            return self.template(*row_tuple)

    def to_obj(self, row_tuple, columns=None):
        # fall back to row_tuple
        if not self._proto:
            if columns:
                new_tuples = collections.namedtuple(self.name, columns, rename=True)
                return self.to_row(row_tuple, new_tuples)
            else:
                return self.to_row(row_tuple)
        # else create objects
        if not columns:
            columns = self.columns
        new_obj = to_obj(self._proto, dict(zip(columns, row_tuple)), *columns, **self._field_map)
        # assign values
        return new_obj

    def ctx(self, ctx):
        return TableContext(self, ctx)

    def __ds_ctx(self):
        return getattr(self._data_source, self.name)

    def select_single(self, where=None, values=None, orderby=None, limit=None, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).select_single(where=where, values=values, orderby=orderby, limit=limit, columns=columns)
        else:
            return self.__ds_ctx().select_single(where=where, values=values, orderby=orderby, limit=limit, columns=columns)

    def select(self, where=None, values=None, orderby=None, limit=None, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).select(where, values, orderby=orderby, limit=limit, columns=columns)
        else:
            return self.__ds_ctx().select(where, values, orderby=orderby, limit=limit, columns=columns)

    def insert(self, *values, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).insert(*values, columns=columns)
        else:
            return self.__ds_ctx().insert(*values, columns=columns)

    def delete(self, where=None, values=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).delete(where=where, values=values)
        else:
            return self.__ds_ctx().delete(where=where, values=values)

    def delete_obj(self, obj, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).delete_obj(obj)
        else:
            return self.__ds_ctx().delete_obj(obj)

    def update(self, new_values, where='', where_values=None, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).update(new_values, where, where_values, columns)
        else:
            return self.__ds_ctx().update(new_values, where, where_values, columns)

    def by_id(self, *args, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).by_id(*args, columns=columns)
        else:
            return self.__ds_ctx().by_id(*args, columns=columns)

    def save(self, obj, columns=None, ctx=None):
        if ctx is not None:
            return self.ctx(ctx).save(obj, columns)
        else:
            return self.__ds_ctx().save(obj, columns)


class DataSource:

    def __init__(self, db_path, schema=None, auto_expand_path=True):
        self.auto_expand_path = auto_expand_path
        self.path = db_path
        self._script_file_map = {}
        self.schema = schema
        self.__default_ctx_obj = None

    def __del__(self):
        if self.__default_ctx_obj is not None:
            self.__default_ctx_obj.close()

    @property
    def path(self):
        return self._filepath

    @path.setter
    def path(self, value):
        if value and str(value).startswith('~') and self.auto_expand_path:
            self._filepath = os.path.expanduser(value)
        else:
            self._filepath = value

    def read_file(self, path):
        if path not in self._script_file_map:
            with open(path, 'r') as script_file:
                self._script_file_map[path] = script_file.read()
        return self._script_file_map[path]

    def open(self, auto_commit=None, schema=None):
        ''' Create a context to execute queries '''
        if schema is None:
            schema = self.schema
        ac = auto_commit if auto_commit is not None else schema.auto_commit if schema else None
        exe = ExecutionContext(self.path, schema=schema, auto_commit=ac)
        # setup DB if required
        if self.path:
            if str(self.path) == ':memory:' or not os.path.isfile(self.path) or os.path.getsize(self.path) == 0:
                logging.getLogger(__name__).warning("DB does not exist at {}. Setup is required.".format(self.path))
                # run setup files
                if schema is not None and schema.setup_files:
                    for file_path in schema.setup_files:
                        logging.getLogger(__name__).info("Executing script file: {}".format(file_path))
                        exe.cur.executescript(self.read_file(file_path))
                # run setup scripts
                if schema is not None and schema.setup_scripts:
                    for script in schema.setup_scripts:
                        exe.cur.executescript(script)
        return exe

    def __default_ctx(self):
        ''' Create a default reusable connection '''
        if self.__default_ctx_obj is None:
            self.__default_ctx_obj = self.open()
        return self.__default_ctx_obj

    def __getattr__(self, name):
        # try to get function from default context
        _ctx = self.__default_ctx()
        if hasattr(_ctx, name):
            return getattr(_ctx, name)
        else:
            raise AttributeError('Attribute {} does not exist'.format(name))


class QueryBuilder(object):

    ''' Default query builder '''
    def __init__(self, schema):
        self.schema = schema

    def build_select(self, table, where=None, orderby=None, limit=None, columns=None):
        query = []
        if isinstance(table, Table):
            if not columns:
                columns = table.columns
            table_name = table.name
        else:
            table_name = str(table)
        query.append("SELECT ")
        query.append(','.join(columns) if columns else '*')
        query.append(" FROM ")
        query.append(table_name)
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
        if isinstance(table, Table):
            table_name = table.name
            if not columns:
                columns = table.columns
        else:
            table_name = str(table)
        if columns:
            if len(values) < len(columns):
                column_names = ','.join(columns[-len(values):]) 
            else:
                column_names = ','.join(columns)
            query = "INSERT INTO %s (%s) VALUES (%s) " % (table_name, column_names, ','.join(['?'] * len(values)))
        else:
            query = "INSERT INTO %s VALUES (%s) " % (table_name, ','.join(['?'] * len(values)))
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
            query = "DELETE FROM {tbl}".format(tbl=table.name)
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
        self.conn = sqlite3.connect(str(path))
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

    def begin(self):
        self.execute("BEGIN")

    def rollback(self):
        self.conn.rollback()

    def commit(self):
        if self.conn:
            try:
                self.conn.commit()
            except Exception as e:
                logging.getLogger(__name__).exception("Cannot commit changes. e = %s" % e)
        else:
            raise sqlite3.OperationalError("Connection was closed. commit() failed")    

    def select_record(self, table, where=None, values=None, orderby=None, limit=None, columns=None):
        ''' Support these keywords where, values, orderby, limit and columns'''
        query = self.schema.query_builder.build_select(table, where, orderby, limit, columns)
        if isinstance(table, Table):
            return table.to_table(self.execute(query, values), columns=columns)
        else:
            return self.execute(query, values)

    def insert_record(self, table, values, columns=None):
        query = self.schema.query_builder.build_insert(table, values, columns)
        self.execute(query, values)
        return self.cur.lastrowid

    def update_record(self, table, new_values, where='', where_values=None, columns=None):
        query = self.schema.query_builder.build_update(table, where, columns)
        return self.execute(query, new_values + where_values if where_values else new_values)

    def delete_record(self, table, where=None, values=None):
        query = self.schema.query_builder.build_delete(table, where)
        logging.getLogger(__name__).debug("Executing: {q} | values={v}".format(q=query, v=values))
        return self.execute(query, values)

    def select_object_by_id(self, table, ids, columns=None):
        _id_cols = table._id_cols if table._id_cols else ('rowid',)
        where = ' AND '.join(['{c}=?'.format(c=c) for c in _id_cols])
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
            logging.getLogger(__name__).debug('Executing q={} | p={}'.format(query, params))
            if params:
                _r = self.cur.execute(query, params)
            else:
                _r = self.cur.execute(query)
            if self.auto_commit:
                self.commit()
            return _r
        except Exception:
            logging.getLogger(__name__).exception('Query failed: q={}, p={}'.format(query, params))
            raise

    def executescript(self, query):
        _r = self.cur.executescript(query)
        if self.auto_commit:
            self.auto_commit()
        return _r

    def executefile(self, file_loc):
        with open(file_loc, 'r') as script_file:
            script_text = script_file.read()
            return self.executescript(script_text)

    def close(self):
        try:
            if self.conn is not None:
                if self.auto_commit:
                    self.commit()
                self.conn.close()
                self.conn = None
        except Exception:
            logging.getLogger(__name__).exception("Error while closing connection")
        finally:
            self.conn = None

    def __getattr__(self, name):
        if name in self.schema._tables:
            tbl = getattr(self.schema, name)
            ctx = TableContext(tbl, self)
            setattr(self, name, ctx)
            return getattr(self, name)
        elif name in dir(self.schema):
            return getattr(self.schema, name, None)
        else:
            raise AttributeError('Attribute {} does not exist'.format(name))

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        try:
            self.close()
        except Exception as e:
            logging.getLogger(__name__).exception("Error was raised while closing DB connection. e = %s" % e)


class Schema(object):
    ''' Contains schema definition of a database
    '''
    def __init__(self, data_source=':memory:', setup_script=None, setup_file=None, auto_commit=True, auto_expand_path=True, strict_mode=False):
        if not data_source:
            data_source = ':memory:'
        if type(data_source) is DataSource:
            self.__data_source = data_source
        else:
            self.__data_source = DataSource(db_path=data_source, schema=self, auto_expand_path=auto_expand_path)
        self.auto_commit = auto_commit
        self.setup_files = []
        if setup_file:
            self.setup_files.append(setup_file)
        self.setup_scripts = []
        if setup_script:
            self.setup_scripts.append(setup_script)
        self._tables = {}
        self.query_builder = QueryBuilder(self)
        self._strict_mode = strict_mode

    def add_file(self, setup_file):
        self.setup_files.append(setup_file)
        return self

    def add_script(self, setup_script):
        self.setup_scripts.append(setup_script)
        return self

    def add_table(self, name, columns=None, proto=None, id_cols=None, alias=None, **field_map):
        ''' Add a new table design to this schema '''
        if not columns:
            columns = []
        tbl_obj = Table(name, *columns, data_source=self.__data_source, proto=proto, id_cols=id_cols, strict_mode=self._strict_mode, **field_map)
        setattr(self, name, tbl_obj)
        self._tables[name] = tbl_obj
        if alias:
            setattr(self, alias, tbl_obj)
            self._tables[alias] = tbl_obj
        return tbl_obj

    @property
    def ds(self):
        return self.__data_source

    def ctx(self):
        ''' Create a new execution context '''
        return self.ds.open(schema=self)

    def __getattr__(self, name):
        # try to get function from default context
        if hasattr(self.__data_source, name):
            return getattr(self.__data_source, name)
        raise AttributeError('Attribute {} does not exist'.format(name))


# TODO: Will rename Schema to Database in future release
Database = Schema


def with_ctx(func=None):
    ''' Auto create a new context if not available '''
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
