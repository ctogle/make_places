#imports
# cython: profile=True
#cimport cython

from libc.math cimport sqrt
from libc.math cimport cos
from libc.math cimport sin
from libc.math cimport tan
from libc.math cimport hypot
import numpy as np
 



stuff = 'hi'

# 3x3 matrix class/functions

cdef class matrix:
    cdef list rows
    cdef list columns

    cdef list columns_from_rows(self, rows):
        cdef vector c1 = vector(rows[0].x,rows[1].x,rows[2].x)
        cdef vector c2 = vector(rows[0].y,rows[1].y,rows[2].y)
        cdef vector c3 = vector(rows[0].z,rows[1].z,rows[2].z)
        cdef list columns = [c1,c2,c3]
        return columns

    cpdef vector multiply(self, vector v):
        cdef float x = dot_c(self.rows[0],v)
        cdef float y = dot_c(self.rows[1],v)
        cdef float z = dot_c(self.rows[2],v)
        v.x = x
        v.y = y
        v.z = z
        return v

    def __init__(self, rows = None, columns = None):
        if rows:
            self.rows = rows
            self.columns = self.columns_from_rows(rows)
        elif columns:
            print 'must use rows for cv.matrix!'
        else:
            z1 = vector(0,0,0)
            z2 = z1.copy()
            z3 = z1.copy()
            rows = [z1,z2,z3]
            self.rows = rows
            self.columns = self.columns_from_rows(rows)

cdef matrix rotation_matrix(float ang,char axis = 'z'):
    if axis == 'z':
        r1 = vector(cos(ang),-sin(ang),0)
        r2 = vector(sin(ang), cos(ang),0)
        r3 = vector(       0,        0,1)
        return matrix(rows = [r1,r2,r3])

# 2d classes/functions

cdef class vector2d:

    def __cinit__(self,float x,float y):
        self.x = x
        self.y = y

    def __str__(self):
        strr = 'vector2d:' + str((self.x,self.y))
        return strr

    cpdef vector2d copy(self):
        cdef vector2d new = vector2d(self.x,self.y)
        return new

    cpdef list to_list(self):
        cdef list new = [self.x,self.y]
        return new

    cpdef vector2d flip(self):
        self.x *= -1.0
        self.y *= -1.0
        return self

    cpdef vector2d translate(self, vector2d tv):
        self.x += tv.x
        self.y += tv.y
        return self

    cpdef vector2d scale(self, vector2d sv):
        self.x *= sv.x
        self.y *= sv.y
        return self

cdef vector2d midpoint2d_c(vector2d v1, vector2d v2):
    cdef float x = (v1.x + v2.x)/2.0
    cdef float y = (v1.y + v2.y)/2.0
    cdef vector2d new = vector2d(x,y)
    return new

cpdef vector2d midpoint2d(vector2d v1, vector2d v2):
    cdef vector2d pt = midpoint2d_c(v1, v2)
    return pt

# 3d classes/functions

cdef class vector:

    def __cinit__(self,float x,float y,float z):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        strr = 'vector:' + str((self.x,self.y,self.z))
        return strr

    #def __eq__(self, other):
    def __richcmp__(self, other, comparator):
    #def __cmp__(self, other):
        xeq = self.x == other.x
        yeq = self.y == other.y
        zeq = self.z == other.z
        return xeq and yeq and zeq

    #def __ne__(self, other):
    #    xeq = self.x != other.x
    #    yeq = self.y != other.y
    #    zeq = self.z != other.z
    #    return xeq or yeq or zeq

    cpdef vector2d xy2d(self):
        cdef vector2d new = vector2d(self.x,self.y)
        return new

    cpdef vector2d xz2d(self):
        cdef vector2d new = vector2d(self.x,self.z)
        return new

    cpdef vector2d yz2d(self):
        cdef vector2d new = vector2d(self.y,self.z)
        return new

    cpdef vector xy(self):
        cdef vector new = vector(self.x,self.y,0.0)
        return new

    cpdef vector xz(self):
        cdef vector new = vector(self.x,0.0,self.z)
        return new

    cpdef vector yz(self):
        cdef vector new = vector(0.0,self.y,self.z)
        return new

    cpdef vector copy(self):
        cdef vector new = vector(self.x,self.y,self.z)
        return new

    cpdef list to_list(self):
        cdef list new = [self.x,self.y,self.z]
        return new

    cpdef tuple to_tuple(self):
        cdef tuple new = (self.x,self.y,self.z)
        return new

    cpdef float magnitude(self):
        cdef float xx = self.x**2
        cdef float yy = self.y**2
        cdef float zz = self.z**2
        cdef float ss = sqrt(xx + yy + zz)
        return ss

    cpdef vector normalize(self):
        cdef float mag = self.magnitude()
        if not mag == 0.0:
            self.x /= mag
            self.y /= mag
            self.z /= mag
        #else:
        #    print 'vector of length 0 cannot be normalized'
        return self

    cpdef vector flip(self):
        self.x *= -1.0
        self.y *= -1.0
        self.z *= -1.0
        return self

    cpdef vector rotate_z(self, float zang):
        cdef matrix rotmat = rotation_matrix(zang)
        rotmat.multiply(self)
        return self

    cpdef vector translate_x(self, float tx):
        self.x += tx
        return self

    cpdef vector translate_y(self, float ty):
        self.y += ty
        return self

    cpdef vector translate_z(self, float tz):
        self.z += tz
        return self

    cpdef vector translate(self, vector tv):
        self.x += tv.x
        self.y += tv.y
        self.z += tv.z
        return self

    cpdef vector scale(self, vector sv):
        self.x *= sv.x
        self.y *= sv.y
        self.z *= sv.z
        return self

    cpdef vector scale_u(self, float s):
        self.x *= s
        self.y *= s
        self.z *= s
        return self

    cpdef vector cross(self, vector v):
        return cross_c(self,v)

    cpdef float dot(self, vector v):
        return dot_c(self,v)

cdef vector zero_c():
    cdef vector new = vector(0,0,0)
    return new

cpdef vector zero():
    return zero_c()

cdef vector one_c():
    cdef vector new = vector(1,1,1)
    return new

cpdef vector one():
    return one_c()

cdef vector flip_c(vector f):
    cdef vector new = vector(-1.0*f.x,-1.0*f.y,-1.0*f.z)
    return new

cpdef vector flip(vector f):
    return flip_c(f)

cdef vector2d flip2d_c(vector2d f):
    cdef vector2d new = vector2d(-1.0*f.x,-1.0*f.y)
    return new

cpdef vector2d flip2d(vector2d f):
    return flip2d_c(f)

cdef vector normalize_c(vector v):
    cdef vector new = v.copy().normalize()
    return new

cpdef vector normalize(vector v):
    return normalize_c(v)

cpdef float magnitude(vector v):
    cdef float xx = v.x**2
    cdef float yy = v.y**2
    cdef float zz = v.z**2
    cdef float ss = sqrt(xx + yy + zz)
    return ss

cdef float dot_c(vector v1, vector v2):
    return v1.x*v2.x + v1.y*v2.y + v1.z*v2.z

cpdef float dot(vector v1, vector v2):
    return dot_c(v1,v2)

cdef vector cross_c(vector v1, vector v2):
    cdef float cx = v1.y*v2.z-v1.z*v2.y
    cdef float cy = v1.z*v2.x-v1.x*v2.z
    cdef float cz = v1.x*v2.y-v1.y*v2.x
    cdef vector res = vector(cx,cy,cz)
    return res

cpdef vector cross(vector v1, vector v2):
    return cross_c(v1,v2)

cdef vector v1_v2_c(vector v1, vector v2):
    cdef float dx = v2.x - v1.x
    cdef float dy = v2.y - v1.y
    cdef float dz = v2.z - v1.z
    cdef vector new = vector(dx,dy,dz)
    return new

cpdef vector v1_v2(vector v1, vector v2):
    cdef vector pt = v1_v2_c(v1, v2)
    return pt

cdef vector vzip_c(vector v1, vector v2):
    cdef float x = v1.x*v2.x
    cdef float y = v1.y*v2.y
    cdef float z = v1.z*v2.z
    return vector(x,y,z)

cpdef vector vzip(vector v1, vector v2):
    cdef vector pt = vzip_c(v1, v2)
    return pt

cdef vector midpoint_c(vector v1, vector v2):
    cdef float x = (v1.x + v2.x)/2.0
    cdef float y = (v1.y + v2.y)/2.0
    cdef float z = (v1.z + v2.z)/2.0
    cdef vector new = vector(x,y,z)
    return new

cpdef vector midpoint(vector v1, vector v2):
    cdef vector pt = midpoint_c(v1, v2)
    return pt

cdef void rotate_z_coords_c(list coords, float ang):
    cdef int ccnt = len(coords)
    cdef int cdx
    cdef vector coo
    for cdx in range(ccnt):
        coo = <vector>coords[cdx]
        coo.rotate_z(ang)

cpdef rotate_z_coords(list coords, float ang):
    rotate_z_coords_c(coords,ang)

cdef void translate_coords_x_c(list coords, float tv):
    cdef int ccnt = len(coords)
    cdef int cdx
    cdef vector coo
    for cdx in range(ccnt):
        coo = <vector>coords[cdx]
        coo.translate_x(tv)

cpdef translate_coords_x(list coords, float tv):
    translate_coords_x_c(coords,tv)

cdef void translate_coords_y_c(list coords, float tv):
    cdef int ccnt = len(coords)
    cdef int cdx
    cdef vector coo
    for cdx in range(ccnt):
        coo = <vector>coords[cdx]
        coo.translate_y(tv)

cpdef translate_coords_y(list coords, float tv):
    translate_coords_y_c(coords,tv)

cdef void translate_coords_z_c(list coords, float tv):
    cdef int ccnt = len(coords)
    cdef int cdx
    cdef vector coo
    for cdx in range(ccnt):
        coo = <vector>coords[cdx]
        coo.translate_z(tv)

cpdef translate_coords_z(list coords, float tv):
    translate_coords_z_c(coords,tv)

cdef void translate_coords_c(list coords, vector t):
    cdef int ccnt = len(coords)
    cdef int cdx
    cdef vector coo
    for cdx in range(ccnt):
        coo = <vector>coords[cdx]
        coo.translate(t)

cpdef translate_coords(list coords, vector t):
    translate_coords_c(coords,t)

cdef void scale_coords_c(list coords, vector t):
    cdef int ccnt = len(coords)
    cdef int cdx
    cdef vector coo
    for cdx in range(ccnt):
        coo = <vector>coords[cdx]
        coo.scale(t)

cpdef scale_coords(list coords, vector t):
    scale_coords_c(coords,t)

cdef vector com(list coords):
    cdef int ccnt = len(coords)
    cdef float ccntf = float(ccnt)
    cdef int cdx = 0
    cdef float x = 0.0
    cdef float y = 0.0
    cdef float z = 0.0
    cdef vector coo
    cdef vector new
    for cdx in range(ccnt):
        coo = <vector>coords[cdx]
        x += coo.x
        y += coo.y
        z += coo.z
    new = vector(x/ccntf,y/ccntf,z/ccntf)
    return new

cpdef vector center_of_mass(list coords):
    return com(coords)

cdef float distance_xy_c(vector v1, vector v2):
    cdef float dx = v2.x - v1.x
    cdef float dy = v2.y - v1.y
    cdef float ds = sqrt(dx**2 + dy**2)
    return ds

cpdef float distance_xy(vector v1, vector v2):
    return distance_xy_c(v1, v2)

cdef float distance_c(vector v1, vector v2):
    cdef vector v1v2 = v1_v2(v1,v2)
    cdef float mag = v1v2.magnitude()
    return mag

cpdef float distance(vector v1, vector v2):
    return distance_c(v1, v2)

cdef int find_closest_xy_c(vector one,list bunch,int bcnt,float close_enough):
    cdef float nearest = 100000000.0
    cdef float ds = nearest
    cdef int bdx
    cdef int ndx = 0
    cdef vector which
    for bdx in range(bcnt):
        which = <vector>bunch[bdx]
        ds = distance_xy_c(one,which)
        if ds < nearest:
            nearest = ds
            ndx = bdx
            if ds <= close_enough:
                return ndx
    return ndx

cpdef int find_closest_xy(vector one,list bunch,int bcnt,float close_enough):
    return find_closest_xy_c(one,bunch,bcnt,close_enough)

cdef float angle_from_xaxis_xy_c(vector v):
    cdef float oldz = v.z
    cdef float angle = angle_from_xaxis_c(v)
    v.z = oldz
    return angle

cpdef float angle_from_xaxis_xy(vector v):
    return angle_from_xaxis_xy_c(v)

#cdef xhat = vector(1,0,0)
#cdef yhat = vector(0,1,0)
#cdef zhat = vector(0,0,1)
xhat  = vector( 1, 0, 0)
yhat  = vector( 0, 1, 0)
zhat  = vector( 0, 0, 1)
nxhat = vector(-1, 0, 0)
nyhat = vector( 0,-1, 0)
nzhat = vector( 0, 0,-1)

cdef float angle_between_xy_c(vector v1, vector v2):
    cdef float alpha1 = angle_from_xaxis_xy_c(v1)
    cdef float alpha2 = angle_from_xaxis_xy_c(v2)
    #if alpha2 - alpha1 > np.pi/2.0:
    #    print 'arpha', v1, v2, alpha1, alpha2
    return alpha2 - alpha1

cpdef float angle_between_xy(vector v1, vector v2):
    return angle_between_xy_c(v1,v2)

cdef float angle_between_c(vector v1, vector v2):
    #cdef float alpha1 = angle_from_xaxis_c(v1)
    #cdef float alpha2 = angle_from_xaxis_c(v2)
    cdef vector n1 = v1.copy().normalize()
    cdef vector n2 = v2.copy().normalize()
    cdef float ang = np.arccos(dot_c(n1,n2))
    #return alpha2 - alpha1
    return ang

cpdef float angle_between(vector v1, vector v2):
    return angle_between_c(v1,v2)

cdef float angle_from_xaxis_c(vector v):
    cdef vector nv = v.copy().normalize()
    cdef float xproj = dot_c(nv,xhat)
    cdef float yproj = dot_c(nv,yhat)
    cdef float ang
    #if xproj == 2.0/np.pi or xproj == 2.0/(3.0*np.pi):
    #    ang = np.arccos(yproj)
    #    if xproj < 0.0: ang = 2.0*np.pi - ang
    #else:
    #    ang = np.arccos(xproj)
    #    if yproj < 0.0: ang = 2.0*np.pi - ang
    ang = np.arccos(xproj)
    if yproj < 0.0: ang = 2.0*np.pi - ang
    return ang

cpdef float angle_from_xaxis(vector v):
    return angle_from_xaxis_c(v)

cpdef bint test_afxa():
    cdef vector v1 = vector(10,0,0)
    cdef vector v2 = vector(10,10,0)
    cdef vector v3 = vector(10,10,10)
    cdef vector v4 = vector(-10,10,0)
    cdef vector v5 = vector(-10,0,0)
    cdef vector v6 = vector(-10,-10,0)
    cdef vector v7 = vector(0,-10,0)
    cdef vector v8 = vector(10,-10,0)
    t1 = str(angle_from_xaxis_c(v1))
    t2 = str(angle_from_xaxis_c(v2))
    t3 = str(angle_from_xaxis_c(v3))
    t4 = str(angle_from_xaxis_c(v4))
    t5 = str(angle_from_xaxis_c(v5))
    t6 = str(angle_from_xaxis_c(v6))
    t7 = str(angle_from_xaxis_c(v7))
    t8 = str(angle_from_xaxis_c(v8))
    print 'ANGLETEST'
    print '\t'.join([t1,t2,t3,t4,t5,t6,t7,t8])

cpdef bint inside(vector pt, list corners):
    poly = [(c.x,c.y) for c in corners]
    x,y = pt.x,pt.y
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



