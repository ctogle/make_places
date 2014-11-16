from distutils.core import setup
from Cython.Build import cythonize

import numpy

from distutils.extension import Extension
from Cython.Distutils import build_ext

#from setuptools import setup,Extension

core_modules = []
ext_modules = [Extension('mp_utils', ['support/make_places_utils.c'])]
#ext_modules = [Extension('mp_utils', ['support/make_places_utils.pyx'])]
#ext_modules = []

setup(
    name="make_places",
    version = '1.0',
    description = "make_places python pkg",
    author = "ctogle",
    author_email = "cogle@vt.edu",
    license = "MIT License",
    long_description = 'procedural city generation', 
    #scripts = ['../modular.py'], 
    packages = ['make_places'], 
    py_modules = core_modules, 
    ext_modules = ext_modules, 
    include_dirs = [numpy.get_include()]
    )




