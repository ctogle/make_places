


#!python33
from os.path import isfile, join
import glob
import os
import re

from setuptools import setup#, Extension
#from distutils.core import setup

import pdb

core_modules = [
	'make_places.blend_in', 
	'make_places.buildings', 
	'make_places.cities', 
	'make_places.floors', 
	'make_places.fundamental', 
	'make_places.make_place', 
	'make_places.primitives', 
	'make_places.roads', 
	'make_places.stairs', 
	'make_places.walls', 
				]

setup(
	name="make_places_blender",
	version = '1.0',
	description = "blender_extension pkg",
	author = "ctogle",
	author_email = "cogle@vt.edu",
	license = "MIT License",
	long_description = '', 
	#scripts = ['../modular.py'], 
	zip_safe = False, 
	packages = ['make_places'], 
	py_modules = core_modules, 
	)




