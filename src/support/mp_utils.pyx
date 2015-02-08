#imports
# cython: profile=False
#cimport cython

cimport mp_vector as cv
import mp_vector as cv
import mp_bboxes as mpbb

from libc.math cimport sqrt
from libc.math cimport cos
from libc.math cimport sin
from libc.math cimport tan
from libc.math cimport hypot

import numpy as np
import random as rm

import cStringIO as sio

stuff = 'hi'

def find_extremes_y(pts):
    lo = pts[0]
    hi = pts[0]
    for pt in pts[1:]:
        if pt.y < lo.y: lo = pt
        if pt.y > hi.y: hi = pt
    return lo,hi

def find_extremes_x(pts):
    lo = pts[0]
    hi = pts[0]
    for pt in pts[1:]:
        if pt.x < lo.x: lo = pt
        if pt.x > hi.x: hi = pt
    return lo,hi

def sweep_search(pts,center,tangent = None):
    # this will behave oddly when `which` would
    #  be a colinear set
    offset = center.copy().flip()
    cv.translate_coords(pts,offset)
    if not tangent is None:
        tangent_rot = cv.angle_from_xaxis_xy(tangent)
        cv.rotate_z_coords(pts,-tangent_rot)
    which = center
    pang = 2*np.pi
    pcnt = len(pts)
    for adx in range(pcnt):
        pt = pts[adx]
        if pt is center: continue
        tpang = cv.angle_from_xaxis_xy(pt)
        if tpang < pang:
            pang = tpang
            which = pt
    if not tangent is None:
        cv.rotate_z_coords(pts,tangent_rot)
    cv.translate_coords(pts,offset.flip())
    return which

def pts_to_convex_xy(pts,start = None):
    # return the corners of the polygon, a subset of pts
    # it could be that pts is all one point or is colinear
    if start is None:new = find_extremes_x(pts)[1]
    else:new = start.copy()
    tang = None
    shape = []
    while not new in shape:
        shape.append(new)
        if len(shape) > 1:
            tang = cv.v1_v2(shape[-2],shape[-1])
        new = sweep_search(pts,new,tang)
    return shape

def inflate(convex, radius):
    enorms = mpbb.get_norms(convex)
    for cdx in range(len(convex)):
        lead = enorms[cdx]
        rear = enorms[cdx-1]
        norm = cv.midpoint(lead,rear).normalize()
        convex[cdx].translate(norm.scale_u(radius))
    return convex

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

cpdef list theta_order(list ppts):
    cdef list ordered = []
    com = cv.com(ppts)
    #cv.translate_coords(ppts,com.flip())

    cdef int pcnt = len(ppts)
    cdef int pdx
    cdef list angles = []
    for pdx in range(pcnt):
        p = ppts[pdx]
        v = cv.v1_v2(com,p)
        a = cv.angle_from_xaxis_xy(v)
        angles.append(a)

    ordered = list(zip(*sorted(zip(angles,ppts)))[1])
    #ordered = zip(*sorted(zip(angles,ppts)))[1]

    #cv.translate_coords(ppts,com.flip())
    #cv.translate_coords(ordered,com)

    return ordered

def subset(superset, sub):
    for su in sub:
        if not su in superset:
             return False
    return True

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

cpdef cv.vector vector_spline(cv.vector c1,cv.vector c2,cv.vector c3,cv.vector c4,int scnt):
    cox = [c1.x,c2.x,c3.x,c4.x]
    coy = [c1.y,c2.y,c3.y,c4.y]
    coz = [c1.z,c2.z,c3.z,c4.z]
    tim = [0.0,1.0,2.0,3.0]
    alpha = 1.0/2.0
    parameterize_time([c1,c2,c3,c4],tim,alpha)
    cox = catmull_rom(cox,tim,scnt)[1:-1]
    coy = catmull_rom(coy,tim,scnt)[1:-1] 
    coz = catmull_rom(coz,tim,scnt)[1:-1] 
    filled = [cv.vector(*i) for i in zip(cox,coy,coz)]
    return filled

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

xheader =\
'''
<mesh>
  <sharedgeometry>
    <vertexbuffer positions="true" normals = "true" colours_diffuse = "false" texture_coord_dimensions_0 = "float2" texture_coords = "1">
'''
cpdef str xml_from_primitive_data(object prim):
    return xml_from_primitive_data_c(prim)

cdef str xml_from_primitive_data_c(object prim):
    cdef list coords = <list>prim.coords
    cdef list ncoords = <list>prim.ncoords
    cdef list ucoords = <list>prim.uv_coords
    cdef int vcnt = len(coords)
    cdef int vdx
    cdef str x
    cdef str y
    cdef str z
    cdef str nx
    cdef str ny
    cdef str nz
    cdef str ux
    cdef str uy
    cdef cv.vector p
    cdef cv.vector n
    cdef cv.vector2d u

    cdef list mats
    cdef int mcnt
    cdef int mdx
    cdef str m

    cdef list f
    cdef int fdx
    cdef int fcnt

    cdef str f1,f2,f3

    cdef str _32bitindices
    if vcnt > 65000:_32bitindices = 'true'
    else:_32bitindices = 'false'
    
    faces = prim.get_vertexes_faces()
    mats = faces.keys()
    mcnt = len(mats)

    sioio = sio.StringIO()
    siowrite = sioio.write
    siowrite(xheader)

    for vdx in range(vcnt):
        p = <cv.vector>coords[vdx]
        x = str(<double>p.x)
        y = str(<double>p.y)
        z = str(<double>p.z)
        n = <cv.vector>ncoords[vdx]
        nx = str(<double>n.x)
        ny = str(<double>n.y)
        nz = str(<double>n.z)
        u = <cv.vector2d>ucoords[vdx]
        ux = str(<double>u.x)
        uy = str(1.0 - <double>u.y)

        siowrite('\t\t\t<vertex>\n\t\t\t\t<position')
        siowrite(' x = "')
        siowrite(x)
        siowrite(' " y = "')
        siowrite(y)
        siowrite('" z = "')
        sioio.write(z)
        sioio.write('" />\n')
        sioio.write('\t\t\t\t<normal x = "')
        sioio.write(nx)
        sioio.write('" y = "')
        sioio.write(ny)
        sioio.write('" z = "')
        sioio.write(nz)
        sioio.write('" />\n')
        sioio.write('\t\t\t\t<texcoord u = "')
        sioio.write(ux)
        sioio.write('" v = "')
        sioio.write(uy)
        sioio.write('" />\n')
        sioio.write('\t\t\t</vertex>\n')

    sioio.write('\t\t</vertexbuffer>\n\t</sharedgeometry>\n\t<submeshes>\n')
    for mdx in range(mcnt):
        m = mats[mdx]
        sioio.write('\t\t<submesh material = "')
        sioio.write(m)
        sioio.write('" usesharedvertices = "true" use32bitindexes = "')
        sioio.write(_32bitindices)
        sioio.write('" operationtype = "triangle_list" >\n')
        sioio.write('\t\t\t<faces>\n')

        mfaces = faces[m]
        fcnt = len(mfaces)
        for fdx in range(fcnt):
            f = <list>mfaces[fdx]
            f1 = str(<int>f[0])
            f2 = str(<int>f[1])
            f3 = str(<int>f[2])
            sioio.write('\t\t\t\t<face v1 = "')
            sioio.write(f1)
            sioio.write('" v2 = "')
            sioio.write(f2)
            sioio.write('" v3 = "')
            sioio.write(f3)
            sioio.write('" />\n')

        sioio.write('\t\t\t</faces>\n\t\t</submesh>\n')

    sioio.write('\t</submeshes>\n</mesh>\n')
    return sioio.getvalue()

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
    for di in range(dices):
        newpts = []
        vcnt = len(verts)
        for tdx in range(vcnt):
            p1 = verts[tdx-1]
            p2 = verts[tdx]
            mpt = cv.midpoint_c(p1,p2)
            newpts.append(p1)
            newpts.append(mpt)
        newpts.append(newpts.pop(0))
        newpts.append(newpts.pop(0))
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






