import mp_utils as mpu

from math import cos
from math import sin
from math import tan
from math import sqrt
import numpy as np
import random as rm

import os, pdb

PI = np.round(np.pi,8)

class base(object):
    def _default_(self, *args, **kwargs):
        key = args[0]
        init = args[1]
        if key in kwargs.keys():init = kwargs[key]
        if not key in self.__dict__.keys():
            self.__dict__[key] = init

def uniq(seq):
    ret = []
    for sq in seq:
        if not sq in ret:
            ret.append(sq)
    return ret

def flatten(unflat_list):
    return [item for sublist in unflat_list for item in sublist]

def quadrant(theta):
    if theta >= 0.0 and theta < PI/2.0: return 1
    elif theta >= PI/2.0 and theta < PI: return 2
    elif theta >= PI and theta < 3.0*PI/2.0: return 3
    elif theta >= 3.0*PI/2.0 and theta < 2.0*PI: return 4
    elif theta >= 2.0*PI: return quadrant(theta % (2.0*PI))
    else: print 'theta', theta, 'not found to be in any quadrant!'
      
def to_rad(deg):
    return (PI/180.0)*deg

def to_deg(rad):
    return (180.0/PI)*rad






