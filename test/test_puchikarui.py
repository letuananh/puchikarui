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
    --
    argparse module:
        https://docs.python.org/3/howto/argparse.html
    PEP 257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/

@author: Le Tuan Anh <tuananh.ke@gmail.com>
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

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2017, puchikarui"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import os
import unittest
import logging
from puchikarui import Schema

#----------------------------------------------------------------------
# Configuration
#----------------------------------------------------------------------

TEST_DIR = os.path.dirname(__file__)
SETUP_FILE = os.path.join(TEST_DIR, 'data', 'init_script.sql')
SETUP_SCRIPT = "INSERT INTO person VALUES ('Chun', 78)"
TEST_DB = os.path.join(TEST_DIR, 'data', 'test.db')


########################################################################

class SchemaDemo(Schema):
    def __init__(self, data_source, setup_script=None, setup_file=SETUP_FILE):
        Schema.__init__(self, data_source, setup_script=setup_script, setup_file=setup_file)
        self.add_table('person', ['name', 'age'])


########################################################################

class TestDemoLib(unittest.TestCase):

    def setUp(self):
        if os.path.isfile(TEST_DB):
            logging.debug("Test DB exists, removing it now")
            os.unlink(TEST_DB)

    def test_basic(self):
        print("Testing basic database actions")
        db = SchemaDemo(TEST_DB, setup_file=SETUP_FILE, setup_script=SETUP_SCRIPT)
        # We can excute SQLite script as usual ...
        db.ds.execute("INSERT INTO person VALUES ('Chen', 15)")
        # Or use this ORM-like method
        # It's not robust yet, just a simple util code block
        # Test insert
        db.person.insert(['Morio', 29])
        db.person.insert(['Kent', 42])
        # Test select data
        persons = db.person.select(where='age > ?', values=[25], orderby='age', limit=10)
        expected = [('Ji', 28), ('Morio', 29), ('Ka', 32), ('Kent', 42), ('Chun', 78)]
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


########################################################################

def main():
    unittest.main()


if __name__ == "__main__":
    main()
