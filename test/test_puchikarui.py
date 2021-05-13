#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing puchikarui library

Latest version can be found at https://github.com/letuananh/puchikarui

References:
    Python documentation:
        https://docs.python.org/
    Python unittest
        https://docs.python.org/3/library/unittest.html

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
'''

# Copyright (c) 2014-2017, Le Tuan Anh <tuananh.ke@gmail.com>

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
import unittest
import logging
from pathlib import Path

import sqlite3
from puchikarui import DataSource, ExecutionContext
from puchikarui import Database, Schema, with_ctx
from puchikarui import escape_like, head_like, tail_like, contain_like
from puchikarui.puchikarui import to_obj, update_obj


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

logging.basicConfig(level=logging.WARNING)
TEST_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
TEST_DATA = TEST_DIR / 'data'
SETUP_FILE = TEST_DATA / 'init_script.sql'
SETUP_SCRIPT = """INSERT INTO person (name, age) VALUES ('Chun', 78); 
INSERT INTO school (name, address) VALUES('Surpreme Coding', 'localhost');"""
TEST_DB = TEST_DATA / 'test.db'


# ------------------------------------------------------------------------------
# Test cases
# ------------------------------------------------------------------------------

class SchemaDemo(Schema):

    def __init__(self, data_source=':memory:', setup_script=SETUP_SCRIPT, setup_file=SETUP_FILE, *args, **kwargs):
        Schema.__init__(self, data_source=data_source, setup_script=setup_script, setup_file=setup_file)
        self.add_table('person', ['ID', 'name', 'age'], proto=Person, id_cols=('ID',))
        self.add_table('hobby').add_fields('pid', 'hobby')
        self.add_table('school', alias='college').add_fields('ID', 'name', 'address')
        self.add_table('diary', ['ID', 'pid', 'text']).set_proto(Diary).set_id('ID').field_map(pid='ownerID', text='content')


class Diary(object):

    def __init__(self, content='', owner=None):
        """

        """
        self.ID = None
        if owner:
            self.owner = owner
            self.ownerID = owner.ID
        else:
            self.owner = None
            self.ownerID = None
        self.content = content

    def __str__(self):
        return "{per} wrote `{txt}`".format(per=self.owner.name if self.owner else '#{}'.format(self.ownerID), txt=self.content)


class Person(object):
    def __init__(self, name='', age=-1):
        self.ID = None
        self.name = name
        self.age = age

    def __str__(self):
        return "#{}: {}/{}".format(self.ID, self.name, self.age)


########################################################################


class TestUtilClass(unittest.TestCase):

    def test_path(self):
        my_home = os.path.expanduser('~')
        expected_loc = os.path.join(my_home, 'tmp', 'test.db')
        ds = DataSource('~/tmp/test.db')
        self.assertEqual(expected_loc, ds.path)

    def test_to_obj(self):
        class Tool:
            def __init__(self, name='', desc=''):
                self.name = name
                self.desc = desc

            def to_dict(self):
                return {'name': self.name, 'desc': self.desc}

        obj_data = {'title': 'Ruler', 'purpose': 'For measuring', 'price': 5}
        t = to_obj(Tool, obj_data, title='name')
        self.assertEqual(t.to_dict(), {'name': 'Ruler', 'desc': ''})
        update_obj(obj_data, t, purpose='desc')
        self.assertEqual(t.to_dict(), {'name': 'Ruler', 'desc': 'For measuring'})

    def test_with_ctx(self):
        class CtxSchema(Schema):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.add_script('''CREATE TABLE test(name TEXT, age INTEGER); INSERT INTO test VALUES ('a', 50)''')
                self.add_table('test', 'name age'.split())

            @with_ctx
            def get_all(self, ctx=None):
                return ctx.test.select()

        x = CtxSchema()
        all = x.get_all()
        self.assertIsNotNone(all)
        self.assertEqual(all[0].name, 'a')
        self.assertEqual(all[0].age, 50)


class TestSchema(unittest.TestCase):

    def test_null_schema(self):
        # path = ''
        ns = Schema('')
        with ns.ctx() as ctx:
            r = ctx.select("SELECT 42")
            self.assertTrue(r)
            self.assertEqual(r[0][0], 42)
        # path = None
        ns2 = Schema(None)
        with ns2.ctx() as ctx:
            r2 = ctx.select("SELECT 42 + 1")
            self.assertTrue(r2)
            self.assertEqual(r2[0][0], 43)
            with self.assertLogs("puchikarui") as logs:
                self.assertRaises(sqlite3.OperationalError, lambda: ctx.execute("INSERT INTO test VALUES(?, ?)", ("a person", 50)))
                _found = False
                for line in logs.output:
                    if 'Query failed' in line:
                        _found = True
                        break
                self.assertTrue(_found)
        ns3 = Schema(":memory:", setup_script=None)
        with ns3.ctx() as ctx:
            r3 = ctx.select("SELECT 42 + 1")
            self.assertTrue(r3)
            self.assertEqual(r3[0][0], 43)
    
    def test_bad_schema(self):
        class BadSchema(Schema):
            def __init__(self, *args, strict_mode=True, **kwargs):
                super().__init__(*args, strict_mode=strict_mode, **kwargs)
                self.add_table('test', 'name class age'.split())
        with self.assertLogs('puchikarui', level='WARNING') as log:
            BadSchema()
            _has_log = False
            for log in log.output:
                if 'Bad database design detected (Table: test' in log:
                    _has_log = True
            self.assertTrue(_has_log)

    def test_no_schema(self):
        class NoSchema(Schema):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.add_script('''CREATE TABLE test(ID INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER);''')
        n = NoSchema()
        for name, age in zip('ABCDE', range(50, 55)):
            n.insert_record('test', (None, f'Person {name}', age))
        rows = [(row['ID'], row['name'], row['age']) for row in n.select_record('test', where='age >= ?', values=(51,))]
        expected = [(2, 'Person B', 51), (3, 'Person C', 52), (4, 'Person D', 53), (5, 'Person E', 54)]
        self.assertEqual(rows, expected)

    def test_accessing_weird_attr(self):
        s = SchemaDemo()
        self.assertRaises(AttributeError, lambda: s.boo())
        self.assertRaises(AttributeError, lambda: print(s.foo))

    def test_auto_commit(self):
        s = SchemaDemo(auto_commit=False)
        with s.ctx() as ctx:
            ctx.auto_commit = False
            ctx.begin()
            ctx.insert_record('school', (None, 'School A1', 'Street 1'))
            ctx.insert_record('school', (None, 'School A2', 'Street 2'))
            ctx.insert_record('school', (None, 'School A3', 'Street 3'))
            self.assertEqual(4, len(ctx.school.select()))
            ctx.rollback()
            self.assertEqual(1, len(ctx.school.select()))
            # call ctx.rollback() again should be safe
            ctx.rollback()
            ctx.insert_record('school', (None, 'School A1', 'Street 1'))
            self.assertEqual(2, len(ctx.school.select()))
            ctx.rollback()  # now rollback again
            self.assertEqual(1, len(ctx.school.select()))
            # force rollback should fail
            with self.assertLogs('puchikarui', level='ERROR') as logs:
                self.assertRaises(sqlite3.OperationalError, lambda: ctx.execute("ROLLBACK"))
                _found = False
                for log in logs.output:
                    if 'cannot rollback - no transaction is active' in log:
                        _found = True
                        break
                self.assertTrue(_found)

    def test_proto(self):
        ds = DataSource(':memory:')
        s = SchemaDemo(ds)
        ds.schema = s
        self.assertEqual(str(s.person), "Table('person', *['ID', 'name', 'age'])")
        p = s.person.select_single()
        self.assertIsInstance(p, Person)
        # select tbl with proto by ID
        p2 = s.select_object_by_id(s.person, (p.ID,))
        self.assertEqual((p.ID, p.name, p.age), (p2.ID, p2.name, p2.age))
        self.assertNotEqual(p, p2)
        # non-existence ID
        p3 = s.person.by_id(None)
        self.assertIsNone(p3)
        # select tuple
        h = s.hobby.select_single()
        self.assertIsInstance(h, tuple)
        school = s.school.select_single()  # first object
        # test to_obj
        objs = s.select_record(s.school)  # all records
        self.assertEqual(school, objs[0])
        # select tuple by id (no proto)
        school_obj = s.school.by_id(school.ID)
        self.assertEqual(school, school_obj)
        self.assertNotEqual(id(school), id(school_obj))


class TestDemoLib(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Setting up tests ...")
        if os.path.isfile(TEST_DB):
            logging.getLogger(__name__).info("Test DB exists, removing it now")
            os.unlink(TEST_DB)

    def test_sqlite_methods(self):
        db = SchemaDemo()
        num = db.ds.select_scalar('SELECT 2')
        self.assertEqual(num, 2)
        nums = db.ds.select_single('SELECT 2, 3, 4')
        self.assertEqual(tuple(nums), (2, 3, 4))
        matrix = db.ds.select('SELECT 1, 2, 3 UNION SELECT 4, 5, 6')
        self.assertEqual(tuple(tuple(row) for row in matrix), ((1, 2, 3), (4, 5, 6)))

    def test_basic(self):
        print("Testing basic database actions")
        db = SchemaDemo(TEST_DB, setup_file=SETUP_FILE, setup_script=SETUP_SCRIPT)
        # We can excute SQLite script as usual ...
        db.ds.execute("INSERT INTO person (name, age) VALUES ('Chen', 15);")
        # Or use this ORM-like method
        # Test insert
        db.person.insert('Kent', 42)
        # Test select data
        persons = db.person.select(where='age > ?', values=[25], orderby='age', limit=10)
        self.assertIsNotNone(persons)
        expected = [('Ji', 28), ('Ka', 32), ('Vi', 33), ('Kent', 42), ('Chun', 78)]
        actual = [(person.name, person.age) for person in persons]
        self.assertEqual(expected, actual)
        # Test select single
        ji = db.person.select_single('name=?', ('Ji',))
        self.assertIsNotNone(ji)
        self.assertEqual(ji.age, 28)
        # Test delete
        db.person.delete(where='age > ?', values=(70,))
        chun = db.person.select_single('name=?', ('Chun',))
        self.assertIsNone(chun)

    def test_execution_context(self):
        db = SchemaDemo(":memory:")
        with db.ctx() as ctx:
            # test select
            ppl = ctx.person.select()
            self.assertEqual(len(ppl), 6)
            # test insert
            ctx.person.insert('Totoro', columns=('name',))  # insert partial data
            ctx.person.insert('Shizuka', 10)  # full record
            p = ctx.person.select_single(where='name=?', values=('Dunno',))
            self.assertIsNone(p)
            # Test update data & select single
            ctx.person.update((10,), "name=?", ("Totoro",), columns=('age',))
            totoro = ctx.person.select_single(where='name=?', values=('Totoro',))
            self.assertEqual(totoro.age, 10)
            # test updated
            ppl = ctx.person.select()
            self.assertEqual(len(ppl), 8)
            # test delete
            ctx.person.delete('age > ?', (70,))
            ppl = ctx.person.select()
            # done!
            expected = [(1, 'Ji', 28), (2, 'Zen', 25), (3, 'Ka', 32), (4, 'Anh', 15), (5, 'Vi', 33), (7, 'Totoro', 10), (8, 'Shizuka', 10)]
            actual = [(person.ID, person.name, person.age) for person in ppl]
            self.assertEqual(expected, actual)

    def test_selective_select(self):
        db = SchemaDemo()  # create a new DB in RAM
        pers = db.person.select(columns=('name',))
        names = [x.name for x in pers]
        self.assertEqual(names, ['Ji', 'Zen', 'Ka', 'Anh', 'Vi', 'Chun'])

    def test_query_builder(self):
        db = SchemaDemo()
        db.person.delete('age > ?', (75,))
        persons = db.person.select()
        ages = [p.age for p in persons]
        for p in persons:
            p.age += 1
            db.person.save(p, ('age',))
        updated_ages = [p.age for p in db.person.select()]
        self.assertEqual(ages, [28, 25, 32, 15, 33])
        self.assertEqual(updated_ages, [29, 26, 33, 16, 34])
        self.assertEqual(len(db.person.select()), 5)
        # update back to before using update_record
        for p in db.person.select():
            p.age -= 1
            db.update_record(db.person, (p.ID, p.name, p.age,), 'id = ?', (p.ID,))
        updated_ages2 = [p.age for p in db.person.select()]
        self.assertEqual(ages, updated_ages2)
        # try insert_object
        db.insert_object(db.person, Person('Boo Boo', 33))
        db.insert_object("person", Person('Boo Boo 2', 34), columns=('name', 'age'))
        self.assertEqual(len(db.person.select()), 7)
        db.update_record(db.person, ('Smurf',), columns=('name',))
        names = [p.name for p in db.person.select()]
        self.assertEqual(names, ['Smurf'] * 7)
        db.person.delete()
        self.assertEqual(len(db.person.select()), 0)

    def test_orm_persistent(self):
        db = SchemaDemo(TEST_DB)
        bid = db.person.save(Person('Buu', 1000))
        buu = db.person.by_id(bid)
        self.assertIsNotNone(buu)
        self.assertEqual(buu.name, 'Buu')
        # insert more stuff
        db.hobby.insert(buu.ID, 'candies')
        db.hobby.insert(buu.ID, 'chocolate')
        db.hobby.insert(buu.ID, 'santa')
        hobbies = db.hobby.select('pid=?', (buu.ID,))
        self.assertEqual({x.hobby for x in hobbies}, {'candies', 'chocolate', 'santa'})
        db.hobby.delete('hobby=?', ('chocolate',))
        hobbies = db.hobby.select('pid=?', (buu.ID,))
        self.assertEqual({x.hobby for x in hobbies}, {'candies', 'santa'})

    def test_orm_with_context(self):
        db = SchemaDemo()  # create a new DB in RAM
        with db.ctx() as ctx:
            p = ctx.person.select_single('name=?', ('Anh',))
            # There is no prototype class for hobby, so a namedtuple will be generated
            hobbies = ctx.hobby.select('pid=?', (p.ID,))
            self.assertIsInstance(p, Person)
            self.assertIsInstance(hobbies[0], tuple)
            self.assertEqual(hobbies[0].hobby, 'coding')
            # insert hobby
            ctx.hobby.insert(p.ID, 'reading')
            hobbies = [x.hobby for x in ctx.hobby.select('pid=?', (p.ID,), columns=('hobby',))]
            self.assertEqual(hobbies, ['coding', 'reading'])
            # now only select the name and not the age
            p2 = ctx.person.select_single('name=?', ('Vi',), columns=('ID', 'name',))
            self.assertEqual(p2.name, 'Vi')
            self.assertEqual(p2.age, -1)
            # test updating object
            p2.name = 'Vee'
            ctx.update_object(db.person, p2, ('name',))
            p2.age = 29
            ctx.update_object(db.person, p2)
            # ensure that data was updated
            p2n = ctx.person.by_id(p2.ID)
            self.assertEqual(p2n.name, 'Vee')
            self.assertEqual(p2n.age, 29)
            self.assertEqual(p2n.ID, p2.ID)

    def test_field_mapping(self):
        content = 'I am better than Emacs'
        new_content = 'I am NOT better than Emacs'
        db = SchemaDemo()
        with db.ctx() as ctx:
            vi = ctx.person.select_single('name=?', ('Vi',))
            diary = Diary(content, owner=vi)
            ctx.diary.save(diary)
            diaries = ctx.diary.select('pid=?', (vi.ID,))
            for d in diaries:
                d.owner = ctx.person.by_id(d.ownerID)
                print(d)
                # test update
                d.content = new_content
                ctx.diary.save(d)
            diary = ctx.diary.by_id(d.ID)
            self.assertEqual(diary.content, new_content)
            print(diary)


class SchemaA(Schema):

    SETUP_FILE = os.path.join(TEST_DATA, 'schemaA.sql')

    def __init__(self, data_source=':memory:', setup_script=None, setup_file=None):
        super().__init__(data_source=data_source, setup_script=setup_script, setup_file=setup_file)
        # setup scripts & files
        self.add_file(SchemaA.SETUP_FILE)
        self.add_script("INSERT INTO person (name, age) VALUES ('potter', 10)")
        # Table definitions
        self.add_table('person', ['ID', 'name', 'age'], proto=Person, id_cols=('ID',))


class SchemaB(Schema):

    SETUP_FILE = os.path.join(TEST_DATA, 'schemaB.sql')

    def __init__(self, data_source=':memory:', setup_script=None, setup_file=None):
        super().__init__(data_source=data_source, setup_script=setup_script, setup_file=setup_file)
        # setup scripts & files
        self.add_file(SchemaB.SETUP_FILE)
        self.add_script("INSERT INTO hobby (name) VALUES ('magic')")
        # Table definitions
        self.add_table('hobby', ['ID', 'name'], proto=Hobby, id_cols=('ID',))
        self.add_table("person_hobby", ["hid", "pid"])


class Hobby(object):

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return "Hobby: {}".format(self.name)


class SchemaAB(SchemaB, SchemaA):

    ''' Execution order: setup_files > setup_scripts
        Schema's file > SchemaA's file > SchemaB's file >
        Schema's script > SchemaA's script > SchemaB's script
        Note: The first class in inheritance list will be executed last
    '''

    def __init__(self, data_source=":memory:", setup_script=None, setup_file=None):
        super().__init__(data_source=data_source, setup_script=setup_script, setup_file=setup_file)
        self.add_script('''INSERT INTO person_hobby VALUES ((SELECT ID FROM hobby WHERE name='magic'), (SELECT ID FROM person WHERE name='potter'));''')

    @with_ctx
    def all_hobby(self, ctx=None):
        return ctx.hobby.select()

    @with_ctx
    def find_hobby(self, name, ctx=None):
        return ctx.hobby.select("name = ?", (name,))


class TestMultipleSchema(unittest.TestCase):

    def test_ms(self):
        db = SchemaAB()
        with db.ctx() as ctx:
            potter = ctx.person.select_single()
            magic = ctx.hobby.select_single()
            link = ctx.person_hobby.select_single()
            self.assertEqual(potter.name, 'potter')
            self.assertEqual(magic.name, 'magic')
            self.assertEqual(link.hid, magic.ID)
            self.assertEqual(link.pid, potter.ID)
            # access schema function from context
            self.assertEqual(len(ctx.all_hobby()), 1)
            self.assertEqual(ctx.find_hobby('magic')[0].name, 'magic')
            print
        pass


class AdvancedDemo(SchemaDemo):

    @with_ctx
    def demo(self, ctx=None):
        p = Person("Buu", 1000)
        p.ID = ctx.person.save(p)
        return ctx.person.by_id(p.ID)


class TestWithContext(unittest.TestCase):

    def test_ms(self):
        db = AdvancedDemo()
        print(db.demo().age)
        with db.ctx() as ctx:
            print(db.demo(ctx=ctx))

    def test_diff_context(self):
        db = SchemaDemo()
        with db.ctx() as ctx:
            # insert 2 persons into default ctx
            id = db.person.insert('Another 1', 100)
            db.person.insert('Another 2', 101)
            db.person.insert('Another 3', 102)
            db.person.delete_obj(db.person.by_id(id))
            # 1 person into the created context
            id2 = db.person.insert('New 1', 50, ctx=ctx)
            id3 = db.person.insert('New 2', 51, ctx=ctx)
            db.person.insert('New 3', 52, ctx=ctx)
            db.person.delete_obj(db.person.by_id(id2, ctx=ctx), ctx=ctx)
            db.person.delete('id=?', (id3,), ctx=ctx)
            # count persons in each context
            persons_ctx1 = db.person.select()
            persons_ctx2 = db.person.select(ctx=ctx)
            self.assertEqual(len(persons_ctx1), 8)
            self.assertEqual(len(persons_ctx2), 7)

    def test_mix_context(self):
        db = SchemaDemo()
        with db.ctx() as ctx:
            p_tuple = ("Another P", 50)
            id = ctx.person.insert(*p_tuple)
            p = ctx.person.by_id(id)
            p.name = "Another Person"
            p.age = 51
            db.person.save(p, ctx=ctx)  # update person info
            p2 = db.person.select_single("id=?", (id,), ctx=ctx)
            self.assertEqual((p.name, p.age), (p2.name, p2.age))

    def test_sep_context(self):
        ctx = ExecutionContext(':memory:', None)
        r = ctx.select('SELECT 2')
        self.assertEqual(r[0][0], 2)
        self.assertIsNotNone(ctx.conn)
        ctx.close()
        self.assertIsNone(ctx.conn)
        ctx.close()
        self.assertRaises(sqlite3.OperationalError, lambda: ctx.commit())

    def test_del_ds(self):
        db = SchemaDemo()
        db.person.select()
        db.close()
        del db

    def test_default_context(self):
        db = SchemaDemo()
        print("Select persons ...")
        persons = db.person.select()
        self.assertEqual(len(persons), 6)
        print("Create a new person")
        p = Person("New Person", 50)
        id = db.person.save(p)
        self.assertEqual(len(db.person.select()), 7)
        # native query
        person_tuples = [tuple(p) for p in db.select('SELECT * FROM person')]
        person_dicts = [dict(p) for p in db.select('SELECT * FROM person')]
        expected_tuples = [(1, 'Ji', 28),
                           (2, 'Zen', 25),
                           (3, 'Ka', 32),
                           (4, 'Anh', 15),
                           (5, 'Vi', 33),
                           (6, 'Chun', 78),
                           (7, 'New Person', 50)]
        expected_dicts = [{'ID': 1, 'name': 'Ji', 'age': 28},
                          {'ID': 2, 'name': 'Zen', 'age': 25},
                          {'ID': 3, 'name': 'Ka', 'age': 32},
                          {'ID': 4, 'name': 'Anh', 'age': 15},
                          {'ID': 5, 'name': 'Vi', 'age': 33},
                          {'ID': 6, 'name': 'Chun', 'age': 78},
                          {'ID': 7, 'name': 'New Person', 'age': 50}]
        self.assertEqual(expected_tuples, person_tuples)
        self.assertEqual(expected_dicts, person_dicts)


class TestPath(unittest.TestCase):

    def test_expand_path(self):
        db = Schema(Path('~/test.db'))
        self.assertEqual(db.path, os.path.expanduser('~/test.db'))
        db2 = Database(Path('~/test.db'), auto_expand_path=False)
        self.assertEqual(str(db2.path), '~/test.db')


class TestHelpers(unittest.TestCase):

    def test_escape(self):
        actual = escape_like('_')
        expect = '@_'
        self.assertEqual(actual, expect)
        actual = escape_like('%')
        expect = '@%'
        self.assertEqual(actual, expect)
        actual = escape_like('@')
        expect = '@@'
        self.assertEqual(actual, expect)
        actual = escape_like('')
        expect = ''
        self.assertEqual(actual, expect)
        actual = escape_like('usual')
        expect = 'usual'
        self.assertEqual(actual, expect)
        self.assertRaises(Exception, lambda: escape_like(None))
        actual = escape_like('%_%@')
        expect = '@%@_@%@@'
        self.assertEqual(actual, expect)
        actual = head_like('a@b')
        expect = 'a@@b%'
        self.assertEqual(actual, expect)
        actual = tail_like('a@b')
        expect = '%a@@b'
        self.assertEqual(actual, expect)
        actual = contain_like('a_@_b')
        expect = '%a@_@@@_b%'
        self.assertEqual(actual, expect)


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
