
import pstats, cProfile

import os, traceback, sys

import pdb

def profile_function(func_):
    cProfile.runctx('func_()',globals(),locals(),'profile.prof')
    s = pstats.Stats('profile.prof')
    s.strip_dirs().sort_stats('time').print_stats()
    os.remove('profile.prof')

