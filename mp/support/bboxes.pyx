from libc.math cimport sqrt

from mp_utils import overlap
from mp_utils import project

stuff = 'hi'

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

class bbox(object):
    def __init__(self, *args, **kwargs):
        self.corners = kwargs['corners']
        if 'position' in kwargs.keys():
            self.position = kwargs['position']
        else: self.position = [0,0,0]
        self.edgenorms = get_norms(self.corners)

    def intersects(self,boxes,box):
        if not type(box) is type([]):box = [box]
        check = separating_axis
        for bo in box:
            for ibox in boxes:
                if check(ibox,bo):
                    return True
        return False















