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
from benchmark1 import SchemaDemo, DB_PATH, __version__


def benchmark2():
    db = SchemaDemo(DB_PATH)
    persons = db.person.select()
    names = {p.name for p in persons}
    for n in names:
        db.person.select("name=?", (n,))


def _timeit():
    repeat = 5
    t = timeit.timeit(lambda: benchmark2(), number=repeat)
    print(f"timeit ({repeat} times): {t} secs | avg: {t / repeat} secs")


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
    print(f"Benchmarking #2: querying data | puchikarui version {__version__}")
    lines = profile_it(benchmark2)
    parent = Path(__file__).absolute().parent
    for idx, l in enumerate(lines):
        if idx >= 6 and 'puchikarui' not in l:
            continue
        print(l.replace(str(parent), parent.name))
    _timeit()
    print(f"Benchmarking #2: querying data | puchikarui version {__version__}")
