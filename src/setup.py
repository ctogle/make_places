from distutils.core import setup
from Cython.Distutils import build_ext
from distutils.extension import Extension
#from Cython.Build import cythonize

import numpy

core_modules = []

ext_modulesc = [
    Extension('mp_utils',  ['support/mp_utils.c']), 
    Extension('mp_bboxes', ['support/mp_bboxes.c']), 
    Extension('mp_vector', ['support/mp_vector.c']),
            ]

setup(
    name="make_places",
    version = '1.0',
    description = "make_places python pkg",
    author = "ctogle",
    author_email = "cogle@vt.edu",
    license = "MIT License",
    long_description = 'procedural city generation', 
    packages = ['make_places'], 
    py_modules = core_modules, 
    ext_modules = ext_modulesc, 
    cmdclass = {'build_ext':build_ext}, 
    include_dirs = [numpy.get_include(),'.']
    )




