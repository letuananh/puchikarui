Puchikarui
==========

A minimalist SQLite helper library for Python 3 which supports ORM features.

[![Total alerts](https://img.shields.io/lgtm/alerts/g/letuananh/puchikarui.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/letuananh/puchikarui/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/letuananh/puchikarui.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/letuananh/puchikarui/context:python)

## Installation

It is available on [PyPI](https://pypi.org/project/puchikarui/) and can be installed using `pip`.

```bash
pip install puchikarui
# or with python -m pip
python3 -m pip install puchikarui
```

## Sample code

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
        self.add_table('person', ['ID', 'name', 'age'], id_cols=('ID',))


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

For more examples please see `puchikarui.demo.py`

```bash
python3 puchikarui.demo.py
```

# Why puchikarui
Although `puchikarui` does provide some ORM-like features, it is *NOT* an ORM library, 
but a helper library that helps working directly SQLite databases more productive (less magic and more control).

If you want ORM features, please consider https://github.com/coleifer/peewee or https://www.sqlalchemy.org/.

