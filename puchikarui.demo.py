#!/usr/bin/env python
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

from puchikarui import Schema, DataSource, Table

class SchemaDemo(Schema):
    def __init__(self, data_source=None):
        Schema.__init__(self, data_source)
        self.add_table('person', ['name', 'age'])

def main():
    db = SchemaDemo.connect('./puchikarui.test.db')
    
    # We can excute SQLite script as usual ...
    db.ds().executescript('''
    DROP TABLE IF EXISTS person; 
    CREATE TABLE person(name, age);
    INSERT INTO person 
    VALUES
     ('Ji', 28)
    ,('Zen', 25)
    ,('Ka', 32)
    ''')
    
    # Or use this ORM-like method
    # It's not robust yet, just a simple util code block
    db.person.insert(['Morio', 29])
    db.person.insert(['Kent', 42])
    persons = db.person.select(where='age > ?', values=[25], orderby='age', limit=10)
    for person in persons:
        print("I'm %s. My age is %d" % (person.name, person.age))
    db.close()
    pass

if __name__ == "__main__":
    main()
