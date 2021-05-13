.. puchikarui documentation master file, created by
   sphinx-quickstart on Thu May 13 15:27:04 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to puchikarui's documentation!
======================================

Welcome to puchikarui's documentation!

A minimalist SQLite helper library for Python 3 which supports ORM features.

|Documentation Status| |Total alerts| |Language grade: Python| |Build Status| |codecov|

Installation
------------

``puchikarui`` is available on
`PyPI <https://pypi.org/project/puchikarui/>`__ and can be installed
using ``pip``.

.. code:: bash

    pip install puchikarui
    # or with python -m pip
    python3 -m pip install puchikarui

Sample code
-----------

.. code:: python

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

For more examples please see ``puchikarui.demo.py``

.. code:: bash

    python3 puchikarui.demo.py

Why puchikarui
--------------

``puchikarui`` is a tiny, 100% pure-Python library that provides extra
functionality to Python 3's
`sqlite3 <https://docs.python.org/3/library/sqlite3.html>`__ module. It
helps working directly with ``sqlite3`` easier, with less magic, and
more control, rather than hiding sqlite3 module away from the users.

Although ``puchikarui`` does provide some ORM-like features, it is *NOT*
an ORM library. If you want ORM features, please consider
`PonyORM <https://ponyorm.org/>`__,
`SQLAlchemy <https://www.sqlalchemy.org/>`__, or
`peewee <https://github.com/coleifer/peewee>`__.

Meaning
-------

The name ``puchikarui`` came from two Japanese words ``プチ`` (puchi)
which means small, and ``軽い`` (karui), which means light, soft, and
gentle.

It represents the motivation for developing this library: a tiny,
lightweight library that makes working with ``sqlite3`` simpler.

.. code:: bash

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

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |Total alerts| image:: https://img.shields.io/lgtm/alerts/g/letuananh/puchikarui.svg?logo=lgtm&logoWidth=18
   :target: https://lgtm.com/projects/g/letuananh/puchikarui/alerts/
.. |Language grade: Python| image:: https://img.shields.io/lgtm/grade/python/g/letuananh/puchikarui.svg?logo=lgtm&logoWidth=18
   :target: https://lgtm.com/projects/g/letuananh/puchikarui/context:python
.. |Build Status| image:: https://travis-ci.org/letuananh/puchikarui.svg?branch=master
   :target: https://travis-ci.org/letuananh/puchikarui
.. |codecov| image:: https://codecov.io/gh/letuananh/puchikarui/branch/master/graph/badge.svg?token=10CEOU8F8M
   :target: https://codecov.io/gh/letuananh/puchikarui
.. |Documentation Status| image:: https://readthedocs.org/projects/puchikarui/badge/?version=latest
   :target: https://puchikarui.readthedocs.io/en/latest/?badge=latest
