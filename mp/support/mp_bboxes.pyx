#imports
# cython: profile=True
#cimport cython
from libc.math cimport sqrt

import mp_vector as cv
cimport mp_vector as cv
#from mp_utils import dot
#from mp_utils import overlap
#from mp_utils import project
#from make_places_utils import overlap
#from make_places_utils import project

stuff = 'hi'

cdef bint overlap_c(cv.vector2d rng1, cv.vector2d rng2):
    if rng1.y < rng2.x: return 0
    elif rng2.y < rng1.x: return 0
    else: return 1

cpdef bint overlap(cv.vector2d rng1, cv.vector2d rng2):
    return overlap_c(rng1, rng2)

cdef cv.vector2d project_c(list verts, cv.vector axis):
    cdef cv.vector v = verts[0]
    cdef float min_ = cv.dot_c(v,axis)
    cdef float max_ = min_
    cdef int vcnt = len(verts)
    cdef int vdx
    cdef float val
    for vdx in range(1,vcnt):
        v = <cv.vector>verts[vdx]
        val = <float>cv.dot_c(v,axis)
        if val < min_: min_ = val
        if val > max_: max_ = val
    return cv.vector2d(min_,max_)

cpdef cv.vector2d project(list verts, cv.vector axis):
    return project_c(verts, axis)

cdef bint separating_axis(bb1,bb2):
    cdef list ns1 = bb1.edgenorms
    cdef list ns2 = bb2.edgenorms
    #cdef list edgenorms = ns1 + ns2
    cdef int egcnt1 = bb1.edgecount
    cdef int egcnt2 = bb2.edgecount
    #cdef int egcnt = len(edgenorms)
    cdef cv.vector edgenorm
    cdef int egdx
    cdef cv.vector2d proj1
    cdef cv.vector2d proj2
    for egdx in range(egcnt1):
        edgenorm = <cv.vector>ns1[egdx]
        proj1 = <cv.vector2d>project_c(bb1.corners,edgenorm)
        proj2 = <cv.vector2d>project_c(bb2.corners,edgenorm)
        if not <bint>overlap_c(proj1,proj2):
            return 1
            #return 0
    for egdx in range(egcnt2):
        edgenorm = <cv.vector>ns2[egdx]
        #edgenorm = <cv.vector>edgenorms[egdx]
        proj1 = <cv.vector2d>project_c(bb1.corners,edgenorm)
        proj2 = <cv.vector2d>project_c(bb2.corners,edgenorm)
        if not <bint>overlap_c(proj1,proj2):
            return 1
            #return 0
    return 0
    #return 1

cdef float distance_to_edge_c(pt,e1,e2):
    print 'not implemented'

cdef list get_norms_c(list verts):
    cdef list norms = []
    cdef int vcnt = len(verts)
    cdef int vdx
    cdef cv.vector v1
    cdef cv.vector v2
    cdef float dx
    cdef float dy
    cdef float dv
    cdef cv.vector norm
    # IS THIS MISSING THE LAST NORM!!!?
    #for vdx in range(1,vcnt):
    for vdx in range(vcnt):
        v1,v2 = verts[vdx-1],verts[vdx]
        dx = v2.x - v1.x
        dy = v2.y - v1.y
        dv = sqrt(dx**2 + dy**2)
        norm = cv.vector(dy/dv,-dx/dv,0)
        norms.append(norm)
    norms.append(norms.pop(0))
    return norms

cpdef list get_norms(list verts):
    return get_norms_c(verts)

cpdef bint intersects(list boxes1, list boxes2):
    cdef int bcnt1 = len(boxes1)
    cdef int bcnt2 = len(boxes2)
    cdef bbox box1
    cdef bbox box2
    cdef int bdx1
    cdef int bdx2
    cdef float br1
    cdef float br2
    for bdx1 in range(bcnt1):
        box1 = <bbox>boxes1[bdx1]
        br1 = box1.radius

        for bdx2 in range(bcnt2):
            box2 = <bbox>boxes2[bdx2]
            br2 = box2.radius

            bbdist = cv.distance_xy_c(box1.center,box2.center)
            if bbdist <= br1 + br2:
                if not separating_axis(box2,box1):
                    return 1
    return 0

cdef class bbox:

    cdef public list corners
    cdef public list edgenorms
    cdef public int edgecount
    cdef public float radius
    cdef public cv.vector center

    def __init__(self, *args, **kwargs):
        # corners are world space coordinates
        self.corners = kwargs['corners']
        #self.corners = [cv.vector(*c) for c in kwargs['corners']]
        self.edgenorms = get_norms_c(self.corners)
        self.edgecount = len(self.edgenorms)
        self.center = cv.com(self.corners)
        cvs = [cv.v1_v2_c(self.center,v) for v in self.corners]
        cdists = [c.magnitude() for c in cvs]
        self.radius = max(cdists)
















