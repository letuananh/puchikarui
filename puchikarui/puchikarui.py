# -*- coding: utf-8 -*-

""" A minimalist SQLite helper library for Python with ORM-like features
"""

# This source code is a part of puchikarui library: https://github.com/letuananh/puchikarui
# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>
# license: MIT

import os
import sys
import sqlite3
import collections
import logging
import functools


# -------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------
from collections import Mapping
from typing import Sequence


def update_obj(source, target, *fields, **field_map):
    source_dict = source.__dict__ if hasattr(source, '__dict__') else source
    if not fields:
        fields = source_dict.keys()
    for f in fields:
        target_f = f if f not in field_map else field_map[f]
        setattr(target, target_f, source_dict[f])


def to_obj(cls, obj_data=None, *fields, **field_map):
    """ prioritize obj_dict when there are conficts """
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
    def __init__(self, name, *columns, data_source=None, proto=None, id_cols: Sequence = None,
                 strict_mode=False, **field_map):
        """ Contains information of a table in the database
            strict_mode -- Warn users if a bad database design is detected (defaulted to False)
        """
        self._strict_mode = strict_mode
        self.name = name
        self.columns = []
        self.add_fields(*columns)
        self._data_source = data_source
        self._proto = proto
        if not id_cols:
            self._id_cols = []
        elif isinstance(id_cols, str):
            self._id_cols = id_cols.split()
        else:
            self._id_cols = id_cols
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

    def ctx(self, ctx) -> 'TableContext':
        return TableContext(self, ctx)

    def __ds_ctx(self) -> 'TableContext':
        return getattr(self._data_source, self.name)

    def select_single(self, where=None, values=None, orderby=None, limit=None, columns=None, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        return ctx.select_single(where=where, values=values, orderby=orderby, limit=limit, columns=columns)

    def select(self, where=None, values=None, orderby=None, limit=None, columns=None, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        return ctx.select(where, values, orderby=orderby, limit=limit, columns=columns)

    def select_iter(self, where=None, values=None, orderby=None, limit=None, columns=None, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        return ctx.select_iter(where, values, orderby=orderby, limit=limit, columns=columns)

    def insert(self, *values, columns=None, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        return ctx.insert(*values, columns=columns)

    def delete(self, where=None, values=None, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        return ctx.delete(where=where, values=values)

    def delete_obj(self, obj, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        return ctx.delete_obj(obj)
        
    def update(self, set_expr, where='', values=None, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        return ctx.update(set_expr, where=where, values=values)

    def update_record(self, new_values, where='', where_values=None, columns=None, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        ctx.update_record(new_values, where, where_values, columns)

    def by_id(self, *args, columns=None, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        return ctx.by_id(*args, columns=columns)

    def save(self, obj, columns=None, ctx=None):
        ctx = self.__ds_ctx() if ctx is None else self.ctx(ctx)
        return ctx.save(obj, columns)


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

    def _read_file(self, path):
        """ [Internal] Read init script file """
        if path not in self._script_file_map:
            with open(path, 'r') as script_file:
                self._script_file_map[path] = script_file.read()
        return self._script_file_map[path]

    def _setup(self, exe, schema):
        """ [Internal] Setup a newly created database """
        logging.getLogger(__name__).warning("DB does not exist at {}. Setup is required.".format(self.path))
        # run setup files
        if schema is not None and schema.setup_files:
            for file_path in schema.setup_files:
                logging.getLogger(__name__).info("Executing script file: {}".format(file_path))
                exe.cur.executescript(self._read_file(file_path))
        # run setup scripts
        if schema is not None and schema.setup_scripts:
            for script in schema.setup_scripts:
                exe.cur.executescript(script)

    def open(self, auto_commit=None, schema=None, **kwargs):
        """ Create a context to execute queries """
        if schema is None:
            schema = self.schema
        if auto_commit is None and schema is not None:
            auto_commit = schema.auto_commit
        exe = ExecutionContext(self.path, schema=schema, auto_commit=auto_commit)
        # setup DB if required
        if self.path and (str(self.path) == ':memory:' or
                          not os.path.isfile(self.path) or os.path.getsize(self.path) == 0):
            self._setup(exe, schema)
        return exe

    def __default_ctx(self):
        """ Create a default reusable connection """
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


class MemorySource(DataSource):

    def __init__(self, db_path, *args, **kwargs):
        super().__init__(db_path, *args, **kwargs)
        self.__conn = None

    def open(self, auto_commit=None, schema=None, force_iterdump=False, **kwargs):
        if schema is None:
            schema = self.schema
        if auto_commit is None and schema is not None:
            auto_commit = schema.auto_commit
        if self.__conn is None:
            logging.getLogger(__name__).info(f"Fetching database into :memory: from file [{self.path}]")
            # fetch from datasource
            source = sqlite3.connect(str(self.path))
            self.__conn = sqlite3.connect(":memory:")
            if sys.version_info < (3, 7) or force_iterdump:
                __cur = self.__conn.cursor()
                for line in source.iterdump():
                    logging.getLogger(__name__).debug(f"Executing {repr(line)}")
                    __cur.execute(line)
            else:
                # use backup if possible
                source.backup(self.__conn)
            source.close()
        return ExecutionContext(self.__conn, schema=schema, auto_commit=auto_commit)


class QueryBuilder(object):

    """ Default query builder """
    def __init__(self, schema):
        self.schema = schema

    @classmethod
    def build_select(cls, table, where=None, orderby=None, limit=None, columns=None) -> str:
        query = []
        if isinstance(columns, str):
            columns = columns.split()
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

    @classmethod
    def build_insert(cls, table, values, columns=None) -> str:
        """ Insert an active record into DB and return lastrowid if available """
        if isinstance(table, Table):
            table_name = table.name
            if not columns:
                columns = table.columns
        else:
            table_name = str(table)
        if isinstance(columns, str):
            columns = columns.split()
        if columns:
            if len(values) < len(columns):
                column_names = ','.join(columns[-len(values):])
            else:
                column_names = ','.join(columns)
            query = "INSERT INTO %s (%s) VALUES (%s) " % (table_name, column_names, ','.join(['?'] * len(values)))
        else:
            query = "INSERT INTO %s VALUES (%s) " % (table_name, ','.join(['?'] * len(values)))
        return query

    @classmethod
    def build_update_record(cls, table, where='', columns=None) -> str:
        table_name = table.name if isinstance(table, Table) else str(table)
        if columns is None:
            columns = table.columns
        set_fields = []
        if isinstance(columns, str):
            columns = columns.split()
        for col in columns:
            set_fields.append("{c}=?".format(c=col))
        if where:
            query = 'UPDATE {t} SET {sf} WHERE {where}'.format(t=table_name, sf=', '.join(set_fields), where=where)
        else:
            query = 'UPDATE {t} SET {sf}'.format(t=table_name, sf=', '.join(set_fields))
        return query

    @classmethod
    def build_delete(cls, table, where=None) -> str:
        table_name = table.name if isinstance(table, Table) else str(table)
        if where:
            query = "DELETE FROM {tbl} WHERE {where}".format(tbl=table_name, where=where)
        else:
            query = "DELETE FROM {tbl}".format(tbl=table_name)
        return query

    @classmethod
    def build_update(cls, table, set_expr, where):
        table_name = table.name if isinstance(table, Table) else str(table)
        if not where and not where.strip():
            return f"UPDATE {table_name} SET {set_expr}"
        else:
            return f"UPDATE {table_name} SET {set_expr} WHERE {where}"


class TableContext(object):
    def __init__(self, table, context):
        self._table = table
        self._context: ExecutionContext = context
        
    def to_table(self, *args, **kwargs):
        return self._table.to_table(*args, **kwargs)

    def select(self, where=None, values=None, **kwargs):
        return self._context.select(self._table, where, values, **kwargs)

    def select_iter(self, where=None, values=None, **kwargs):
        return self._context.select_iter(self._table, where, values, **kwargs)

    def select_single(self, where=None, values=None, **kwargs):
        result = next(self._context.select_iter(self._table, where, values, **kwargs), None)
        return result

    def insert(self, *values, columns=None):
        return self._context.insert_record(self._table, values, columns)

    def update_record(self, new_values, where='', where_values=None, columns=None):
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

    def update(self, set_expr, where='', values=None):
        return self._context.update(self._table, set_expr, where=where, values=values)


class ExecutionContext(object):
    """ Create a context to work with a schema which closes connection when destroyed
    """
    def __init__(self, source, schema: 'Database',
                 auto_commit=True, row_factory=sqlite3.Row):
        if isinstance(source, sqlite3.Connection):
            # reuse connection object
            self.conn = source
        else:
            # create a new connection object
            self.conn = sqlite3.connect(str(source))
        if row_factory is not None:
            self.conn.row_factory = row_factory
        self.cur = self.conn.cursor()
        self.schema = schema
        self.auto_commit = auto_commit
        self.__closed = False

    def double(self, **kwargs) -> 'ExecutionContext':
        """ Create a parallel execution context object with a different cursor

        Note: The connection object and schema are identical to the source execution context.
        This function is helpful when multiple cursors are needed at the same time,
        for example:

        >>> with db.ctx() as ctx:
        ...     for id in ctx.double(row_factory=None).execute("SELECT id FROM person"):
        ...         p = ctx.person.by_id(id)
        ...         # more complex queries go here ...
        """
        return ExecutionContext(self.conn, self.schema, **kwargs)

    @property
    def is_open(self):
        return not self.__closed

    def buckmode(self):
        """ Optimized setting for buck insert
        """
        self.cur.execute("PRAGMA cache_size=80000000")
        self.cur.execute("PRAGMA journal_mode=MEMORY")
        self.cur.execute("PRAGMA temp_store=MEMORY")
        # self.cur.execute("PRAGMA count_changes=OFF")
        return self

    def begin(self):
        """ Start a transaction """
        self.execute("BEGIN")

    def rollback(self):
        """ Roll back a transaction """
        self.conn.rollback()

    def commit(self):
        """ Commit changes made in current transaction """
        if self.is_open and self.conn is not None:
            self.conn.commit()
        else:
            raise sqlite3.OperationalError("Connection was closed. commit() failed")

    def select(self, table, where=None, values=None, orderby=None, limit=None, columns=None):
        """ Support these keywords where, values, orderby, limit and columns"""
        if isinstance(table, Table):
            return tuple(x for x in self.select_iter(table, where, values, orderby, limit, columns))
        else:
            query = QueryBuilder.build_select(table, where, orderby, limit, columns)
            return self.execute(query, values).fetchall()

    def select_iter(self, table, where=None, values=None, orderby=None, limit=None, columns=None):
        """ Support these keywords where, values, orderby, limit and columns"""
        query = QueryBuilder.build_select(table, where, orderby, limit, columns)
        if isinstance(table, Table):
            for row_tuple in self.execute(query, values):
                yield table.to_obj(row_tuple, columns=columns)
        else:
            return self.execute(query, values)

    def insert(self, table, values=None, columns=None, **kwargs):
        if values is None:
            values = kwargs
        if isinstance(values, Mapping):
            if kwargs:
                values.update(kwargs)
            if columns is None:
                columns = values.keys()
            values = tuple(values.values())
        query = QueryBuilder.build_insert(table, values, columns)
        self.execute(query, values)
        return self.cur.lastrowid

    def insert_record(self, *args, **kwargs):
        return self.insert(*args, **kwargs)

    def update_record(self, table, new_values, where='', where_values=None, columns=None):
        query = QueryBuilder.build_update_record(table, where, columns)
        return self.execute(query, new_values + where_values if where_values else new_values)

    def delete_record(self, table, where=None, values=None):
        query = QueryBuilder.build_delete(table, where)
        logging.getLogger(__name__).debug("Executing: {q} | values={v}".format(q=query, v=values))
        return self.execute(query, values)

    def select_object_by_id(self, table, ids, columns=None):
        _id_cols = table._id_cols if table._id_cols else ('rowid',)
        where = ' AND '.join(['{c}=?'.format(c=c) for c in _id_cols])
        return next(self.select_iter(table, where, ids, columns=columns), None)

    def insert_object(self, table, obj_data, columns=None, field_map=None):
        if not columns and isinstance(table, Table):
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

    def query_row(self, query, params=None):
        """ Select, fetch, and return the first row """
        return self.execute(query, params).fetchone()
    
    def query_all(self, query, params=None):
        """ Select, fetch and return all rows """
        return self.execute(query, params).fetchall()

    def query_scalar(self, query, params=None):
        """ Select, fetch and return the first value of the first row """
        return self.query_row(query, params)[0]

    def update(self, table, set_expr, where='', values=None):
        query = QueryBuilder.build_update(table, set_expr, where=where)
        return self.execute(query, values)

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
        """ Execute an SQL script (update, delete, etc.) """
        _r = self.cur.executescript(query)
        if self.auto_commit:
            self.commit()
        return _r

    def executefile(self, file_loc):
        """ Execute SQL scripts in a text file """
        with open(file_loc, 'r') as script_file:
            script_text = script_file.read()
            return self.executescript(script_text)

    def close(self):
        """ Try closing current transaction """
        if self.is_open:
            if self.auto_commit:
                self.commit()
            self.conn.close()
            self.conn = None
            self.__closed = True

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
        if self.is_open:
            self.close()


class Database(object):
    """ Represents a database
    """
    def __init__(self, data_source=':memory:', setup_script=None, setup_file=None, auto_commit=True, auto_expand_path=True, strict_mode=False):
        if not data_source:
            data_source = ':memory:'
        if isinstance(data_source, DataSource):
            self.__data_source = data_source
            self.__data_source.auto_commit = auto_commit
            self.__data_source.schema = self
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
        """ Add a new table design to this schema """
        if not columns:
            columns = []
        elif isinstance(columns, str):
            # warning?
            columns = columns.split()
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
        """ Create a new execution context """
        return self.ds.open(schema=self)

    def __getattr__(self, name):
        # try to get function from default context
        if hasattr(self.__data_source, name):
            return getattr(self.__data_source, name)
        raise AttributeError('Attribute {} does not exist'.format(name))


# TODO: Will rename Schema to Database in future release (>= 0.3)
Schema = Database


def with_ctx(func=None):
    """ Auto create a new context if not available """
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
