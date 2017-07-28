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

from puchikarui import Schema

#----------------------------------------------------------------------
# CONFIGURATION
#----------------------------------------------------------------------

SETUP_FILE = './test/data/init_script.sql'
TEST_DB = './test/data/demo.db'


#----------------------------------------------------------------------
# DATA STRUCTURES
#----------------------------------------------------------------------

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
        self.add_table('person', ['ID', 'name', 'age'], ('ID',), proto=Person)
        self.add_table('hobby', ['pid', 'hobby'])


#----------------------------------------------------------------------
# MAIN
#----------------------------------------------------------------------

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
    print("There are {} people.".format(len(persons)))
    for person in persons:
        print("%s is %d years old." % (person.name, person.age))
    # update data
    buu.age += 1
    db.person.save(buu)
    print("Buu aged now => {}".format(db.person.by_id(buu.ID)))


if __name__ == "__main__":
    main()
