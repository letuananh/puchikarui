#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Puchikarui demo script

Latest version can be found at https://github.com/letuananh/puchikarui
"""

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

import os
from puchikarui import Schema

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

MY_DIR = os.path.dirname(__file__)
SETUP_FILE = os.path.join(MY_DIR, 'test/data/init_script.sql')
TEST_DB = os.path.join(MY_DIR, 'test/data/demo_orm.db')


# ----------------------------------------------------------------------
# Data Structures
# ----------------------------------------------------------------------

class Person(object):
    def __init__(self, name='', age=-1):
        self.ID = None
        self.name = name
        self.age = age

    def __str__(self):
        return "#{}: {}/{}".format(self.ID, self.name, self.age)


class SchemaDemo(Schema):

    def __init__(self, data_source, setup_file=SETUP_FILE):
        Schema.__init__(self, data_source, setup_file=setup_file)
        self.add_table('person', 'ID name age', id_cols='ID', proto=Person)
        self.add_table('hobby', ['pid', 'hobby'])


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    db = SchemaDemo(TEST_DB)
    goku = db.person.select_single('name=?', ('Goku',))
    if not goku:
        db.person.insert('Goku', 20)
    buu = db.person.select_single('name=?', ('Buu',))
    if not buu:
        db.person.save(Person('Buu', 1000))
    # test select
    persons = db.person.select(orderby='age')
    print(f"There are {len(persons)} people.")
    for person in persons:
        print(f"{person.name} is {person.age} years old.")
    # update data
    buu = db.person.select_single('name=?', ('Buu',))
    buu.age += 1
    db.person.save(buu)
    print(f"Aged Buu => {db.person.by_id(buu.ID)}")


if __name__ == "__main__":
    main()
