#imports
# cython: profile=True
#cimport cython

from libc.math cimport sqrt
from libc.math cimport cos
from libc.math cimport sin
from libc.math cimport tan
from libc.math cimport hypot

#from libc.math cimport log
#from libc.math cimport sin as sin
#from libc.math cimport cos as cos
#from math import sin as sin
#from math import cos as cos
# from libc.math cimport fmax
# from math import log

#import random
import numpy as np
import random as rm

#from numpy import pi

cpdef list v1_v2(list v1, list v2):
    cdef list v1_v2_ = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
    return v1_v2_

cpdef float magnitude(list vect):
    return sqrt(dot(vect,vect))

cpdef float distance_xy(list v1,list v2):
    cdef float dx
    cdef float dy
    cdef float ds
    dx = v2[0] - v1[0]
    dy = v2[1] - v1[1]
    ds = (dx**2 + dy**2)**(0.5)
    return ds

cpdef float distance(list v1,list v2):
    return magnitude(v1_v2(v1,v2))

cpdef list center_of_mass(list coords):
    xs,ys,zs = zip(*coords)
    #xme = np.round(np.mean(xs),8)
    xme = np.mean(xs, dtype = np.float32)
    yme = np.mean(ys, dtype = np.float32)
    zme = np.mean(zs, dtype = np.float32)
    return [xme,yme,zme]

cpdef list cross(list v1, list v2):
    cdef float cx = v1[1]*v2[2]-v1[2]*v2[1]
    cdef float cy = v1[2]*v2[0]-v1[0]*v2[2]
    cdef float cz = v1[0]*v2[1]-v1[1]*v2[0]
    cdef list res = [cx,cy,cz]
    return res

cpdef float dot(list v1, list v2):
    cdef float xp
    cdef float yp
    cdef float zp
    cdef float res
    xp = v1[0]*v2[0]
    yp = v1[1]*v2[1]
    zp = v1[2]*v2[2]
    res = xp + yp + zp
    return res

cpdef tuple project(list verts, list axis):
    cdef float min_ = dot(verts[0],axis)
    cdef float max_ = min_
    cdef int vcnt = len(verts)
    cdef int vdx
    cdef float val
    for vdx in range(1,vcnt):
    #for v in verts[1:]:
        v = verts[vdx]
        val = dot(v,axis)
        if val < min_: min_ = val
        if val > max_: max_ = val
    return (min_,max_)

cpdef bint overlap(rng1,rng2):
    if max(rng1) < min(rng2): return 0
    elif max(rng2) < min(rng1): return 0
    else: return 1

cpdef bint separating_axis(bb1,bb2):
    cdef list ns1 = bb1.edgenorms
    cdef list ns2 = bb2.edgenorms
    cdef list edgenorms = ns1 + ns2
    cdef list edgenorm
    cdef int egcnt = len(edgenorms)
    cdef int egdx
    cdef tuple proj1
    cdef tuple proj2
    for egdx in range(egcnt):
        edgenorm = edgenorms[egdx]
        proj1 = project(bb1.corners,edgenorm)
        proj2 = project(bb2.corners,edgenorm)
        if not overlap(proj1,proj2): return 0
    return 1

cpdef list get_norms(list verts):
    cdef list norms = []
    #zhat = [0,0,1]
    cdef int vcnt = len(verts)
    cdef int vdx
    cdef list v1
    cdef list v2
    cdef float dx
    cdef float dy
    cdef float dv
    cdef list norm
    for vdx in range(1,vcnt):
        v1,v2 = verts[vdx-1],verts[vdx]
        dx = v2[0] - v1[0]
        dy = v2[1] - v1[1]
        dv = sqrt(dx**2 + dy**2)
        norm = [dy/dv,-dx/dv,0]
        norms.append(norm)
    return norms

cpdef tuple find_closest_xy(list one,list bunch):
    cdef int bcnt = len(bunch)
    cdef float nearest = 100000000.0
    cdef float ds = nearest
    cdef int bdx
    cdef int ndx = 0
    for bdx in range(bcnt):
        ds = distance_xy(one,bunch[bdx])
        if ds < nearest:
            nearest = ds
            ndx = bdx
    return bunch[ndx],nearest,ndx

cpdef list find_in_radius(list pt,list verts,float radius = 10):
    cdef list in_ = []
    cdef int vcnt = len(verts)
    cdef int vdx
    for vdx in range(vcnt):
        vt = verts[vdx]
        if distance(pt,vt) < radius: in_.append(vt)
    return in_

cpdef list parameterize_time(list points,list time,float alpha):
    cdef float total = 0.0
    cdef int idx
    cdef list v1v2
    for idx in range(1,4):
        v1v2 = v1_v2(points[idx-1],points[idx])
        total += magnitude(v1v2)**(2.0*alpha)
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

cpdef list translate_coords(list coords, list vect):
    for coo in coords:
        for dx in range(3):
            coo[dx] += vect[dx]
    return coords




# finish these!
cpdef list scale_coords(list coords, list vect):
    for coo in coords:
        for dx in range(3):
            coo[dx] *= vect[dx]
    return coords

def row_major_multiply(M, coo):
    rcoox = dot(M[0],coo)
    rcooy = dot(M[1],coo)
    rcooz = dot(M[2],coo)
    return [rcoox, rcooy, rcooz]

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

def rotate_z_matrix(ang_z):
    M_z = [
        [cos(ang_z),-sin(ang_z), 0], 
        [sin(ang_z), cos(ang_z), 0], 
        [         0,          0, 1], 
            ]
    return M_z

def rotate_z_coord(coord, ang_z):
    M_z = rotate_z_matrix(ang_z)
    rot_coo = row_major_multiply(M_z, coord)
    return rot_coo

cpdef list rotate_z_coords(list coords, float ang_z):
    cdef list M_z = rotate_z_matrix(ang_z)
    cdef int cocnt = len(coords)
    cdef int cdx
    #for coo in coords:
    for cdx in range(cocnt):
        coo = coords[cdx]
        rot_coo = row_major_multiply(M_z, coo)
        coo[:] = rot_coo
    return coords

cpdef list scale_vector(list vect, list sv):
    cdef int dx
    for dx in range(3):
        vect[dx] *= sv[dx]
    return vect

cpdef list translate_vector(list vect, list tv):
    cdef int dx
    for dx in range(3):
        vect[dx] += tv[dx]
    return vect

cpdef list normalize(list vect):
    cdef float mag = magnitude(vect)
    if mag == 0: return [0,0,0]
    return [v/mag for v in vect]





