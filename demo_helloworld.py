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
from puchikarui import Database

if os.path.isfile("test/data/demo.db"):
    os.unlink("test/data/demo.db")
db = Database("test/data/demo.db",
              setup_script="""CREATE TABLE person(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER);
              """)
# create new persons
for name, age in zip("ABCDE", range(20, 25)):
    db.insert("person", name=f"Person {name}", age=age)
# update data
db.update("person", "age = age + 2", where="age >= 20")
# Select data using parameters
for person in db.select("person", where="age > ?", values=(23,)):
    print(dict(person))
