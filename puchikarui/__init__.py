# -*- coding: utf-8 -*-

'''
Puchi Karui - Minimalist SQLite ORM engine for Python

Latest version can be found at https://github.com/letuananh/puchikarui

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
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

__author__ = "Le Tuan Anh"
__email__ = "tuananh.ke@gmail.com"
__copyright__ = "Copyright 2014, puchikarui"
__credits__ = []
__license__ = "MIT License"
__description__ = "A minimalist SQLite wrapper library for Python which supports ORM features."
__url__ = "https://github.com/letuananh/puchikarui"
__maintainer__ = "Le Tuan Anh"
__version_major__ = "0.1"
__version__ = "{}a1".format(__version_major__)
__version_long__ = "{} - Alpha".format(__version_major__)
__status__ = "Prototype"

########################################################################

from .puchikarui import Schema, ExecutionContext, DataSource, Table, with_ctx

__all__ = ["Schema", "ExecutionContext", "DataSource", "Table", "with_ctx"]
