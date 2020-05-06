#!/usr/bin/python3.5
"""A setup.py-style script to Cythonize text_generator.py. This is not necessary
to use the module in the first place, but may result in performance benefits if
it is done.

Requires Cython and a C compiler, of course.

This script is copyright 2020 by Patrick Mooney. You are free to use it for any
purpose whatsoever.
"""


from setuptools import setup
from Cython.Build import cythonize

setup(
    name='text generator',
    ext_modules=cythonize("text_generator.py"),
    zip_safe=False,
)
