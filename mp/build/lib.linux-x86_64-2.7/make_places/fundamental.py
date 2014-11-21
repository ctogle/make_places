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

class bbox(base):
    def __init__(self, *args, **kwargs):
        self._default_('corners',[],**kwargs)
        self._default_('position',[0,0,0],**kwargs)
        self._default_('edgenorms',
            mpu.get_norms(self.corners),**kwargs)

    def intersects(self,boxes,box):
        if not type(box) is type([]):box = [box]
        check = mpu.separating_axis
        for bo in box:
            for ibox in boxes:
                if check(ibox,bo):
                    return True
        return False



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





def point_slope________(x1,x2,y1,y2):
    if x1 == x2: return None
    else: return (y2-y1)/(x2-x1)

def line_y_intersect_________(pt,m):
    if m is None: return None
    x = pt[0]
    y = pt[1]
    run = x*m
    return y - run

def in_range______(x, rng):
    in_ = x > min(rng) and x < max(rng)
    return in_

def inside_________(pt, corners):
    poly = [(c[0],c[1]) for c in corners]
    x,y = pt[0],pt[1]
    n = len(poly)
    inside = False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

###DONT TRUST THIS
def pt_on_segment__________(pt,seg):
    v1v2 = v1_v2(seg[0],pt)
    v1v3 = v1_v2(seg[0],seg[1])
    alpha = angle_between(v1v2,v1v3)
    if abs(alpha) <= 0.01: return True
    else: return False

def segments_intersect_________(s1,s2):
    m1 = point_slope(s1[0][0],s1[1][0],s1[0][1],s1[1][1])
    m2 = point_slope(s2[0][0],s2[1][0],s2[0][1],s2[1][1])
    if m1 == m2:
        #print('segments with same slope', m1,m2)
        return False
    b1 = line_y_intersect(s1[0],m1)
    b2 = line_y_intersect(s2[0],m2)
    if b1 is None:
        x_int = s1[0][0]
        y_int = m2*x_int + b2
    elif b2 is None:
        x_int = s2[0][0]
        y_int = m1*x_int + b1
    else:
        x_int = (b1 - b2)/(m2 - m1)
        y_int = m1*x_int + b1
    rng_chks = [
        in_range(x_int, (s1[0][0], s1[1][0])), 
        in_range(x_int, (s2[0][0], s2[1][0])), 
        in_range(y_int, (s1[0][1], s1[1][1])), 
        in_range(y_int, (s2[0][1], s2[1][1])), 
        ]
    if False in rng_chks: return False
    # are x_int,y_int within bounds of either seg?
    #print('segmentsDOintersect!',s1,s2)
    return True

def in_region_______(regi,pt):
    for dx in range(len(regi)):
        if not in_range(pt[dx],regi[dx]):
            return False
    return True

def flip_____(v1):
    return [-1*v for v in v1]

def dice_edges_______(verts, dices = 3):
    vcnt = len(verts)
    for di in range(dices):
        newpts = []
        for tdx in range(1,vcnt):
            pair = verts[tdx-1],verts[tdx]
            mpt = mpu.midpoint(*pair)
            newpts.extend([pair[0],mpt])
        newpts.extend([newpts[-1],mpu.midpoint(newpts[-1],verts[0])])
        verts = newpts
    return verts






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





















