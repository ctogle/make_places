import mp_utils as mpu
from mp_utils import dot
from mp_utils import magnitude

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

class vertex(object):
    def __init__(self, pos, normal, uv):
        self.pos = pos
        self.normal = normal
        self.uv = uv

#def uniq(seq):
#    # Not order preserving
#    keys = {}
#    for e in seq:
#        keys[e] = 1
#    return keys.keys()

def uniq(seq):
    ret = []
    for sq in seq:
        if not sq in ret:
            ret.append(sq)
    return ret

def flatten(unflat_list):
    return [item for sublist in unflat_list for item in sublist]

def angle_between_xy(v1, v2):
    alpha1 = angle_from_xaxis_xy(v1)
    alpha2 = angle_from_xaxis_xy(v2)
    if alpha2 - alpha1 > PI/2:
        print('arpha', v1, v2, alpha1, alpha2)
    return alpha2 - alpha1

def angle_between(v1, v2):
    alpha1 = angle_from_xaxis(v1)
    alpha2 = angle_from_xaxis(v2)
    return alpha2 - alpha1

def angle_from_zaxis_xz(v1):
    fakev1 = v1[:]
    fakev1[1] = 0
    return angle_from_zaxis(fakev1)

def angle_from_xaxis_xy(v1):
    fakev1 = v1[:]
    fakev1[2] = 0
    return angle_from_xaxis(fakev1)

def angle_from_zaxis(v1):
    v1 = mpu.normalize(v1)
    length = magnitude(v1)
    z_hat = [0,0,1]
    z_proj = dot(v1, z_hat)
    sign = -1 if v1[1] < 0 else 1
    if z_proj == 0:ang = sign*PI/2.0
    elif z_proj < length and z_proj > -length:
        ang = sign*np.arccos(z_proj)
    elif z_proj < 0:ang = PI
    else:ang = 0.0
    return ang    

def angle_from_xaxis(v1):
    v1 = mpu.normalize(v1)
    length = magnitude(v1)
    x_hat = [1,0,0]
    x_proj = dot(v1, x_hat)
    sign = -1 if v1[1] < 0 else 1
    if x_proj == 0:ang = sign*PI/2.0
    elif x_proj < length and x_proj > -length:
        ang = sign*np.arccos(x_proj)
    elif x_proj < 0:ang = PI
    else:ang = 0.0
    return ang    

def to_rad(deg):
    return (PI/180.0)*deg

def to_deg(rad):
    return (180.0/PI)*rad





















