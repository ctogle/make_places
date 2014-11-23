from libc.math cimport sqrt

 



stuff = 'hi'

cdef class vector:

    cdef float x
    cdef float y
    cdef float z

    def __cinit__(self,float x,float y,float z):
        self.x = x
        self.y = y
        self.z = z

    cpdef list to_list(self):
        cdef list new = [self.x,self.y,self.z]
        return new

    cpdef float magnitude(self):
        cdef float xx = self.x**2
        cdef float yy = self.y**2
        cdef float zz = self.z**2
        cdef float ss = sqrt(xx + yy + zz)
        return ss

    cpdef normalize(self):
        cdef float mag = self.magnitude()
        if not mag == 0.0:
            self.x /= mag
            self.y /= mag
            self.z /= mag

    cpdef translate(self, vector tv):
        self.x += tv[0]
        self.y += tv[1]
        self.z += tv[2]

    cpdef scale(self, vector sv):
        self.x *= sv[0]
        self.y *= sv[1]
        self.z *= sv[2]

cdef vector v1_v2(vector v1, vector v2):
    cdef float dx = v2[0] - v1[0]
    cdef float dy = v2[1] - v1[1]
    cdef float dz = v2[2] - v1[2]
    cdef vector new = vector(dx,dy,dz)
    return new

cdef vector vzip(vector v1, vector v2):
    cdef float x = v1.x*v2.x
    cdef float y = v1.y*v2.y
    cdef float z = v1.z*v2.z
    return vector(x,y,z)

cdef vector midpoint(vector v1, vector v2):
    cdef float x = (v1.x + v2.x)/2.0
    cdef float y = (v1.y + v2.y)/2.0
    cdef float z = (v1.z + v2.z)/2.0
    cdef vector new = vector(x,y,z)
    return new

cdef vector com(list coords):
    cdef int ccnt = len(coords)
    cdef int cdx = 0
    cdef float cdxn = 1.0

    cdef float x = 0.0
    cdef float y = 0.0
    cdef float z = 0.0

    cdef vector coo
    for cdx in range(ccnt):
        cdxn += 1.0
        coo = <vector>coords[cdx]
        x = (x*(cdxn-1.0) + coo.x)/cdxn
        y = (y*(cdxn-1.0) + coo.y)/cdxn
        z = (z*(cdxn-1.0) + coo.z)/cdxn
    return vector(x,y,z)

cpdef vector center_of_mass(list coords):
    return com(coords)

cdef float distance_xy(vector v1, vector v2):
    cdef float dx = v2[0] - v1[0]
    cdef float dy = v2[1] - v1[1]
    cdef float ds = sqrt(dx**2 + dy**2)
    return ds

cdef float distance(vector v1, vector v2):
    cdef vector v1v2 = v1_v2(v1,v2)
    cdef float mag = v1v2.magnitude()
    return mag

cdef int find_closest_xy(list one,list bunch,int bcnt,float close_enough):
    cdef float nearest = 100000000.0
    cdef float ds = nearest
    cdef int bdx
    cdef int ndx = 0
    cdef vector which
    for bdx in range(bcnt):
        which = <vector>bunch[bdx]
        ds = distance_xy(one,which)
        if ds < nearest:
            nearest = ds
            ndx = bdx
            if ds <= close_enough:
                return ndx
    return ndx

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



