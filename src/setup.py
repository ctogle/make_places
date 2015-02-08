from distutils.core import setup
from Cython.Distutils import build_ext
from distutils.extension import Extension
#from Cython.Build import cythonize

import numpy

core_modules = []

'''#
ext_modules = [
    Extension('mp_utils',  ['make_places/core/support/mp_utils.pyx']), 
    Extension('mp_bboxes', ['make_places/core/support/mp_bboxes.pyx']), 
    Extension('mp_vector', ['make_places/core/support/mp_vector.pyx','make_places/core/support/mp_vector.pxd']),
            ]

def ext_setup(extname,extmods):
    setup(name = extname,ext_modules = [extmods],
        cmdclass = {'built_ext':build_ext},
        include_dirs = [numpy.get_include(),'.'])

ext_setup('mp_utils',ext_modules[0])
ext_setup('mp_bboxes',ext_modules[1])
ext_setup('mp_vector',ext_modules[2])
#ext_setup('mp_terrain',ext_modules[3])
'''#

ext_modulesc = [
    Extension('mp_utils',  ['support/mp_utils.c']), 
    Extension('mp_bboxes', ['support/mp_bboxes.c']), 
    Extension('mp_vector', ['support/mp_vector.c']),#,'make_places/core/support/mp_vector.pxd']),
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




