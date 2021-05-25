# -*- coding: utf-8 -*-

""" Benchmark insert and select
"""

# This source code is a part of puchikarui library: https://github.com/letuananh/puchikarui
# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>
# license: MIT

import io
from pathlib import Path
from itertools import cycle
import timeit
import cProfile
import pstats

from puchikarui import __version__
from puchikarui import Schema

# create a file DB
DB_PATH = Path("test/data/test_benchmark.db")
SETUP_SCRIPT = """
CREATE TABLE person(
       ID INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT NOT NULL,
       age INTEGER
);
CREATE TABLE hobby (
     pid INTEGER NOT NULL,
     hobby TEXT,
     FOREIGN KEY (pid) REFERENCES person(ID) ON DELETE CASCADE ON UPDATE CASCADE
);
"""


class SchemaDemo(Schema):

    def __init__(self, data_source=':memory:', setup_script=SETUP_SCRIPT, *args, **kwargs):
        Schema.__init__(self, data_source=data_source, setup_script=setup_script)
        self.add_table('person', ['ID', 'name', 'age'], proto=Person, id_cols=('ID',))
        self.add_table('hobby').add_fields('pid', 'hobby')


class Person(object):
    def __init__(self, name='', age=-1):
        self.ID = None
        self.name = name
        self.age = age

    def __str__(self):
        return "#{}: {}/{}".format(self.ID, self.name, self.age)

    def to_dict(self):
        return {'ID': self.ID,
                'name': self.name,
                'age': self.age}


def benchmark1(row_count=10000):
    if DB_PATH.is_file():
        DB_PATH.unlink()
    db = SchemaDemo(DB_PATH)
    # insert 10k rows
    db.buckmode()
    for idx, name_seed in zip(range(row_count), cycle(range(65, 91))):
        # if idx % 500 == 0:
        #     print(f"Current: {idx}")
        name = f"Person {chr(name_seed)}{idx}"
        age = idx % 70
        db.person.save(Person(name, age))
    db.commit()
    # select from DB
    persons = db.person.select()
    names = {p.name for p in persons}
    for n in names:
        db.person.select("name=?", (n,))


def _timeit():
    repeat = 5
    t = timeit.timeit(lambda: benchmark1(), number=repeat)
    print(f"timeit ({repeat} times): {t}")


def profile_it(benchmark_func, sort_fields=["cumulative", "filename", "ncalls"]):
    pr = cProfile.Profile()
    pr.enable()
    benchmark_func()
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s)
    if sort_fields:
        ps.sort_stats(*sort_fields)
    ps.print_stats()
    lines = s.getvalue().splitlines()
    return lines


if __name__ == "__main__":
    print(f"Benchmarking puchikarui version {__version__}")
    lines = profile_it(benchmark1)
    parent = Path(__file__).absolute().parent
    for idx, l in enumerate(lines):
        if idx >= 6 and 'puchikarui' not in l:
            continue
        print(l.replace(str(parent), parent.name))
    _timeit()
    print(f"Benchmarking puchikarui version {__version__}")
