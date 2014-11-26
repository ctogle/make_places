

from distutils.core import setup, Extension

module1 = Extension('mp_math', sources = ['mp_math.c'])
setup (name = 'mp_math',
       version = '1.0',
       description = 'This is a demo package',
       ext_modules = [module1])


