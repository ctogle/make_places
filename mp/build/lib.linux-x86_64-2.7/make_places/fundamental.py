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

def center_of_mass(coords):
    xs,ys,zs = zip(*coords)
    #xme = np.round(np.mean(xs),8)
    xme = np.mean(xs, dtype = np.float32)
    yme = np.mean(ys, dtype = np.float32)
    zme = np.mean(zs, dtype = np.float32)
    return [xme,yme,zme]

def translate_coords(coords, vect):
    for coo in coords:
        for dx in range(3):
            coo[dx] += vect[dx]
    return coords

def scale_coords(coords, vect):
    for coo in coords:
        for dx in range(3):
            coo[dx] *= vect[dx]
    return coords

def rotate_y_coords(coords, ang_y):
    M_y = [
        [cos(ang_y), 0,-sin(ang_y)], 
        [         0, 1,          0], 
        [sin(ang_y), 0, cos(ang_y)], 
            ]
    for coo in coords:
        rot_coo = row_major_multiply(M_y, coo)
        coo[:] = rot_coo
    return coords

def rotate_z_coords(coords, ang_z):
    M_z = [
        [cos(ang_z),-sin(ang_z), 0], 
        [sin(ang_z), cos(ang_z), 0], 
        [         0,          0, 1], 
            ]
    for coo in coords:
        rot_coo = row_major_multiply(M_z, coo)
        coo[:] = rot_coo
    return coords

def scale_vector(vect, sv):
    for dx in range(3):
        vect[dx] *= sv[dx]
    return vect

def translate_vector(vect, tv):
    for dx in range(3):
        vect[dx] += tv[dx]
    return vect

#should this happen in place?
def normalize(vect):
    mag = magnitude(vect)
    if mag == 0: return [0,0,0]
    return [v/mag for v in vect]
    #return [np.round(v/mag,4) for v in vect]

def v1_v2(v1, v2):
    v1_v2_ = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
    return v1_v2_

def point_slope(x1,x2,y1,y2):
    if x1 == x2: return None
    else: return (y2-y1)/(x2-x1)

def line_y_intersect(pt,m):
    if m is None: return None
    x = pt[0]
    y = pt[1]
    run = x*m
    return y - run

def in_range(x, rng):
    in_ = x > min(rng) and x < max(rng)
    return in_

def inside(pt, corners):
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
def pt_on_segment(pt,seg):
    v1v2 = v1_v2(seg[0],pt)
    v1v3 = v1_v2(seg[0],seg[1])
    alpha = angle_between(v1v2,v1v3)
    if abs(alpha) <= 0.01: return True
    else: return False

def segments_intersect(s1,s2):
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

def in_region(regi,pt):
    for dx in range(len(regi)):
        if not in_range(pt[dx],regi[dx]):
            return False
    return True

def midpoint(p1,p2):
    def me(x,y): return (x+y)/2.0
    return [me(x,y) for x,y in zip(p1,p2)]

def distance_xy(v1,v2):
    dx = v2[0] - v1[0]
    dy = v2[1] - v1[1]
    ds = sqrt(dx**2 + dy**2)
    return ds

def distance(v1,v2):
    return magnitude(v1_v2(v1,v2))

def magnitude(vect):
    return sqrt(dot(vect,vect))

def cross(v1, v2):
  return [
      v1[1]*v2[2]-v1[2]*v2[1], 
      v1[2]*v2[0]-v1[0]*v2[2], 
      v1[0]*v2[1]-v1[1]*v2[0]]

def dot(v1, v2):
    xp = v1[0]*v2[0]
    yp = v1[1]*v2[1]
    zp = v1[2]*v2[2]
    return xp + yp + zp

def flip(v1):
    return [-1*v for v in v1]

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
    v1 = normalize(v1)
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
    v1 = normalize(v1)
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

def row_major_multiply(M, coo):
    rcoox = dot(M[0],coo)
    rcooy = dot(M[1],coo)
    rcooz = dot(M[2],coo)
    return [rcoox, rcooy, rcooz]

def find_corners(pos, length, width):
    c1, c2, c3, c4 = pos[:], pos[:], pos[:], pos[:]
    c2[0] += length
    c3[0] += length
    c3[1] += width
    c4[1] += width
    return [c1, c2, c3, c4]

def dice_edges(verts, dices = 3):
    vcnt = len(verts)
    for di in range(dices):
        newpts = []
        for tdx in range(1,vcnt):
            pair = verts[tdx-1],verts[tdx]
            mpt = midpoint(*pair)
            newpts.extend([pair[0],mpt])
        newpts.extend([newpts[-1],midpoint(newpts[-1],verts[0])])
        verts = newpts
    return verts

def offset_faces(faces, offset):
    for fa in faces:
        for fx in range(len(fa)):
            fa[fx] += offset
    return faces

def find_closest_xy(one,bunch):
    ds = [mpu.distance_xy(one,b) for b in bunch]
    #ds = [distance_xy(one,b) for b in bunch]
    dx = ds.index(min(ds))
    return bunch[dx],ds[dx],dx

def find_in_radius(pt,verts,radius = 10):
    in_ = []
    for vt in verts:
        if distance(pt,vt) < radius: in_.append(vt)
    return in_

class vertex(object):
    def __init__(self, pos, normal, uv):
        self.pos = pos
        self.normal = normal
        self.uv = uv

class bbox(base):
    def __init__(self, *args, **kwargs):
        self._default_('corners',[],**kwargs)
        self._default_('position',[0,0,0],**kwargs)

    def intersects(self,boxes,box):
        if not type(box) is type([]):box = [box]
        check = separating_axis
        for bo in box:
            for ibox in boxes:
                if check(ibox,bo):
                    return True
        return False

def get_norms(verts):
    norms = []
    #zhat = [0,0,1]
    for vdx in range(1, len(verts)):
        v1,v2 = verts[vdx-1],verts[vdx]
        #v1_v2_ = normalize(v1_v2(v1,v2))
        #norm = normalize(cross(v1_v2_,zhat))
        dx = v2[0] - v1[0]
        dy = v2[1] - v1[1]
        dv = sqrt(dx**2 + dy**2)
        norm = [dy/dv,-dx/dv,0]
        norms.append(norm)
    return norms

def project(verts, axis):
    min_ = dot(verts[0],axis)
    max_ = min_
    for v in verts[1:]:
        val = dot(v,axis)
        if val < min_: min_ = val
        if val > max_: max_ = val
    return [min_,max_]
    
def overlap(rng1,rng2):
    if max(rng1) < min(rng2): return False
    elif max(rng2) < min(rng1): return False
    else: return True

def separating_axis(bb1,bb2):
    ns1 = get_norms(bb1.corners)
    ns2 = get_norms(bb2.corners)
    edgenorms = ns1 + ns2
    for edgenorm in edgenorms:
        proj1 = project(bb1.corners,edgenorm)
        proj2 = project(bb2.corners,edgenorm)
        if not overlap(proj1,proj2):
            return False
    return True

def break_elements(elements):
    def prep(elem):
        elms = [elem.transform(child) for child in elem.children]
        return elms
    elements = [prep(el) for el in elements]
    return [item for sublist in elements for item in sublist]














