#imports
# cython: profile=False
#cimport cython

cimport mp_vector as cv
import mp_vector as cv

from libc.math cimport sqrt
from libc.math cimport cos
from libc.math cimport sin
from libc.math cimport tan
from libc.math cimport hypot

#from libc.math cimport log
# from libc.math cimport fmax
# from math import log

import numpy as np
import random as rm

#from numpy import pi

stuff = 'hi'

def make_corners(pos,l,w,theta):
    hl = l/2.0
    hw = w/2.0
    corners = [
        cv.vector(-hl,-hw,0), 
        cv.vector( hl,-hw,0), 
        cv.vector( hl, hw,0), 
        cv.vector(-hl, hw,0)]
    cv.rotate_z_coords(corners,theta)
    cv.translate_coords(corners,pos)
    return corners





cpdef list parameterize_time(list points,list time,float alpha):
    cdef float total = 0.0
    cdef int idx
    cdef list v1v2
    for idx in range(1,4):
        #v1v2 = v1_v2(points[idx-1],points[idx])
        #total += magnitude(v1v2)**(2.0*alpha)
        total += cv.v1_v2_c(points[idx-1],points[idx]).magnitude()**(2.0*alpha)
        time[idx] = total

cpdef list catmull_rom(list P,list T,int tcnt):
    cdef int j
    cdef int t
    cdef float tt
    cdef float p
    cdef list spl = P[:1]
    for j in range(1, len(P)-2):  # skip the ends
        for t in range(tcnt):  # t: 0 .1 .2 .. .9
            tt = float(t)/tcnt
            tt = T[1] + tt*(T[2]-T[1])
            p = spline([P[j-1], P[j], P[j+1], P[j+2]],
                    [T[j-1], T[j], T[j+1], T[j+2]],tt)
            spl.append(p)
    spl.extend(P[-2:])
    return spl

cpdef float spline(list p,list time,float t):
    L01 = p[0] * (time[1] - t) / (time[1] - time[0]) + p[1] * (t - time[0]) / (time[1] - time[0])
    L12 = p[1] * (time[2] - t) / (time[2] - time[1]) + p[2] * (t - time[1]) / (time[2] - time[1])
    L23 = p[2] * (time[3] - t) / (time[3] - time[2]) + p[3] * (t - time[2]) / (time[3] - time[2])
    L012 = L01 * (time[2] - t) / (time[2] - time[0]) + L12 * (t - time[0]) / (time[2] - time[0])
    L123 = L12 * (time[3] - t) / (time[3] - time[1]) + L23 * (t - time[1]) / (time[3] - time[1])
    C12 = L012 * (time[2] - t) / (time[2] - time[1]) + L123 * (t - time[1]) / (time[2] - time[1])
    return C12

cdef float midmean(float x, float y):
    return (x + y) / 2.0

cpdef list midpoint(list p1,list p2):
    #def me(x,y): return (x+y)/2.0
    return [midmean(x,y) for x,y in zip(p1,p2)]

cpdef list offset_faces(list faces, int offset):
    #cdef list fa
    cdef int fdx
    cdef int tfdx
    cdef int fcnt = len(faces)
    cdef int tfcnt
    for fdx in range(fcnt):
        fa = faces[fdx]
        tfcnt = len(fa)
        for tfdx in range(tfcnt):
            fa[tfdx] += offset
    return faces


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
    in_ = x > rng[0] and x < rng[1]
    #in_ = x > min(rng) and x < max(rng)
    return in_

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
        if   dx == 0: val = pt.x
        elif dx == 1: val = pt.y
        elif dx == 2: val = pt.z
        if not in_range(val,regi[dx]):
        #if not in_range(pt[dx],regi[dx]):
            return False
    return True

cpdef list dice_edges(list verts, int dices = 3):
    vcnt = len(verts)
    for di in range(dices):
        newpts = []
        for tdx in range(1,vcnt):
            p1 = verts[tdx-1]
            p2 = verts[tdx]
            mpt = cv.midpoint_c(p1,p2)
            #pair = verts[tdx-1],verts[tdx]
            #mpt = cv.midpoint_c(*pair)
            #newpts.extend([p1,mpt])
            newpts.append(p1)
            newpts.append(mpt)
        p1 = newpts[-1]
        p2 = verts[0]
        mpt = cv.midpoint_c(p1,p2)
        newpts.append(p1)
        newpts.append(mpt)
        #newpts.extend([newpts[-1],cv.midpoint_c(newpts[-1],verts[0])])
        verts = newpts
    return verts

cpdef float clamp(float val, float floor, float ceiling):
    if val < floor: return floor
    elif val > ceiling: return ceiling
    else: return val

def inside____(pt, corners):
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






