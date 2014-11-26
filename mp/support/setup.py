from distutils.core import setup
from Cython.Build import cythonize

import numpy

from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules1 = ('mp_utils', [Extension('mp_utils',['mp_utils.pyx'])])
ext_modules2 = ('mp_bboxes', [Extension('mp_bboxes',['mp_bboxes.pyx'])])
ext_modules3 = ('mp_vector', [Extension('mp_vector',['mp_vector.pyx', 'mp_vector.pxd'])])
ext_modules4 = ('mp_terrain', [Extension('mp_terrain',['mp_terrain.pyx','mp_utils.pyx'])])
#ext_modules1 = ('mp_utils', [Extension('mp_utils',['make_places_utils.pyx'])])
#ext_modules2 = ('mp_bboxes', [Extension('mp_bboxes',['bboxes.pyx'])])
#ext_modules3 = ('mp_vector', [Extension('mp_vector',['vector.pyx', 'vector.pxd'])])
#ext_modules4 = ('mp_terrain', [Extension('mp_terrain',['terrain.pyx'])])

def ext_setup(ext_name, ext_modules):
    setup(name = ext_name, 
      	ext_modules = ext_modules, 
      	cmdclass = {'build_ext': build_ext}, 
      	include_dirs = [numpy.get_include(),'.'])

ext_setup(*ext_modules1)
ext_setup(*ext_modules2)
ext_setup(*ext_modules3)
ext_setup(*ext_modules4)

#python setup.py build_ext --inplace


