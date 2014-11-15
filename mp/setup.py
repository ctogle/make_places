from setuptools import setup,Extension

core_modules = []
#ext_modules = [Extension('mp_utils', ['make_places_utils.pyx'])]
ext_modules = []

setup(
    name="make_places",
    version = '1.0',
    description = "make_places python pkg",
    author = "ctogle",
    author_email = "cogle@vt.edu",
    license = "MIT License",
    long_description = 'procedural city generation', 
    #scripts = ['../modular.py'], 
    zip_safe = False, 
    packages = ['make_places'], 
    py_modules = core_modules, 
    ext_modules = ext_modules, 
    )




