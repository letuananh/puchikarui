Puchikarui
==========

**Puchikarui** is a minimalist SQLite helper library for Python 3 which supports ORM features.

[![Documentation Status](https://readthedocs.org/projects/puchikarui/badge/?version=latest)](https://puchikarui.readthedocs.io/en/latest/?badge=latest)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/letuananh/puchikarui.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/letuananh/puchikarui/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/letuananh/puchikarui.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/letuananh/puchikarui/context:python)
[![Build Status](https://travis-ci.org/letuananh/puchikarui.svg?branch=master)](https://travis-ci.org/letuananh/puchikarui)
[![codecov](https://codecov.io/gh/letuananh/puchikarui/branch/main/graph/badge.svg?token=10CEOU8F8M)](https://codecov.io/gh/letuananh/puchikarui)

## Sample code

```python
from puchikarui import Database

setup_script = """
CREATE TABLE person(
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT NOT NULL,
   age INTEGER);"""
db = Database("test/data/demo.db",
              setup_script=setup_script)
# create new persons
for name, age in zip("ABCDE", range(20, 25)):
    db.insert("person", name=f"Person {name}", age=age)
# update data
db.update("person", "age = age + 2", where="age >= 20")
# Select data using parameters
for person in db.select("person", where="age > ?", values=(23,)):
    print(dict(person))
```

## Sample ORM code

```python
from puchikarui import Database

INIT_SCRIPT = '''
CREATE TABLE person (
       ID INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT,
       age INTEGER
);
'''

class PeopleDB(Database):
  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_script(INIT_SCRIPT)
        self.add_table('person', 'ID name age', id_cols='ID')


db = PeopleDB('test.db')
people = db.person.select()
# create sample people records in the first run
if not people:
  print("Creating people records ...")
  for name, age in zip('ABCDE', range(20, 25)):
    db.person.insert(f'Person {name}', age)
  people = db.person.select()

print("All people")
print("----------------------")
for person in people:
  print(person.ID, person.name, person.age)
```

For more information please see [puchikarui documentation](https://puchikarui.readthedocs.io).

## Installation

`puchikarui` is available on [PyPI](https://pypi.org/project/puchikarui/) and can be installed using `pip`.

```bash
pip install puchikarui
```

## Why puchikarui

`puchikarui` is a tiny, 100% pure-Python library that provides extra functionality to Python 3's [sqlite3](https://docs.python.org/3/library/sqlite3.html) module. 
It helps working directly with `sqlite3` easier, with less magic, and more control, rather than hiding sqlite3 module away from the users.

Although `puchikarui` does provide some ORM-like features, it is *NOT* an ORM library. 
If you want ORM features, please consider [PonyORM](https://ponyorm.org/), [SQLAlchemy](https://www.sqlalchemy.org/), or [peewee](https://github.com/coleifer/peewee).

### Features

- Working with simple use cases is simple (e.g. just create a new DB object with `db = Database('file.db')` and start working)
- Database can be loaded into memory before querying for boosting up performance
- connections and cursors can be created, used, and closed automatically or manually
- Flexible execution context management (single or multiple cursors)
- Use up-to-date database best practices (using parameters to prevent SQL injection, optimize settings for buck insert, et cetera)
- Defining database schemas is simple

## Meaning

The name `puchikarui` came from two Japanese words `プチ` (puchi) which means small, and `軽い` (karui), which means light, soft, and gentle.

It represents the motivation for developing this library: a tiny, lightweight library that makes working with `sqlite3` simpler.

```bash
$ python3 -m jamdict lookup "プチ"
========================================
Found entries
========================================
Entry: 1115200 | Kj:   | Kn: プチ
--------------------
1. small ((prefix))

$ python3 -m jamdict lookup "軽い"
========================================
Found entries
========================================
Entry: 1252560 | Kj:  軽い | Kn: かるい, かろい
--------------------
1. light (i.e. not heavy)/feeling light (i.e. offering little resistance, moving easily) ((adjective (keiyoushi)))
2. light (i.e. of foot)/effortless/nimble/agile ((adjective (keiyoushi)))
3. non-serious/minor/unimportant/trivial ((adjective (keiyoushi)))
4. slight/small/gentle/soft/easy/lighthearted (e.g. joke) ((adjective (keiyoushi)))
5. easy/simple ((adjective (keiyoushi)))
6. indiscriminate ((adjective (keiyoushi)))
```
