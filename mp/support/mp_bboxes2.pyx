
import make_places.fundamental as fu

from libc.math cimport sqrt

import mp_vector as cv
cimport mp_vector as cv
import mp_utils as mpu
#cimport mp_utils as mpu

import matplotlib.pyplot as plt

# this is new implementation of xy bboxes
# it should have names properly identified as xy if they are xy only
# it should have one bb class which supports hierarchy and plotting
# and both a quick and a verbose intersection check
# bboxes only contain world space data





cdef class isection:

    cdef public list members

    cpdef bint true(self):
        owners = []
        for me in self.members:
            if not me in owners:
                owners.append(me)

cdef class bbox:

    cdef public cv.vector center
    cdef public list children
    cdef public list corners
    cdef public list edgenorms
    cdef public int edgecount
    cdef public float radius
    cdef public bint bottomlevel

    def _plot_corners(self, color = 'black'):
        x = [c.x for c in self.corners]
        y = [c.y for c in self.corners]
        x.append(x[0])
        y.append(y[0])
        plt.plot(x,y,color = color,marker = 'o')

    def _plot(self, colors = None):
        if colors is None:
            colors = ['black','red','green','blue','purple']
        color = colors.pop(0)
        self._plot_corners(color)
        for ch in self.children:
            ch._plot(colors[:])

    def __init__(self,corners = None,children = None):
        if children is None:
            self.bottomlevel = True
            self.corners = corners
            self.children = []
        else:
            self.bottomlevel = False
            self.children = children
            if corners is None:
                self.corners = self._project_children_xy()
            else:self.corners = corners
                
        self.edgenorms = cv.line_normals(self.corners)
        self.edgecount = len(self.edgenorms)
        self.center = cv.com(self.corners)
        cdists = [cv.distance(self.center,v) for v in self.corners]
        self.radius = max(cdists)

    def _intersect_xy(self,other,isect = None):
        if not self._separating_axis(other):
            if isect is None:isect = []
            if self.bottomlevel:
                if not self in isect:isect.append(self)
            else:
                for ch in self.children:
                    isect = ch._intersect_xy(other,isect)
            if other.bottomlevel:
                if not other in isect:isect.append(other)
            else:
                for och in other.children:
                    isect = och._intersect_xy(self,isect)
        return isect

    def _separating_axis(self,other):
        # binary - does self overlap other
        return separating_axis(self,other)

    '''#
    def _separating_axis_many(self,other):
        # binary - do any of self.children overlap other.children
        return separating_axis_many(self.children,other.children)
    '''#
      
    def _project_children_xy(self):
        all_verts = []
        for ch in self.children:
            all_verts.extend(ch.corners)
        xproj = project(all_verts,cv.xhat)
        yproj = project(all_verts,cv.yhat)
        c1 = cv.vector(xproj.x,yproj.x,0)
        c2 = cv.vector(xproj.y,yproj.x,0)
        c3 = cv.vector(xproj.y,yproj.y,0)
        c4 = cv.vector(xproj.x,yproj.y,0)
        return [c1,c2,c3,c4]

    def _add_children(self,*children):
        self.children = []
        for ch in children:
            self.children.append(ch)
        if self.children:
            self.bottomlevel = False
            self.corners = self._project_children_xy()

    def _lose_children(self):
        self.children = []
        self.bottomlevel = True

    def __str__(self):
        strr = 'bbox with corners:\n'
        for c in self.corners:
            strr += '\t' + c.__str__()
        return strr

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

cdef bint separating_axis_c(bbox bb1,bbox bb2):
    cdef list ns1 = bb1.edgenorms
    cdef list ns2 = bb2.edgenorms
    cdef int egcnt1 = bb1.edgecount
    cdef int egcnt2 = bb2.edgecount
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
    for egdx in range(egcnt2):
        edgenorm = <cv.vector>ns2[egdx]
        proj1 = <cv.vector2d>project_c(bb1.corners,edgenorm)
        proj2 = <cv.vector2d>project_c(bb2.corners,edgenorm)
        if not <bint>overlap_c(proj1,proj2):
            return 1
    return 0

cpdef bint separating_axis(bbox bb1,bbox bb2):
    return separating_axis_c(bb1,bb2)

'''#
cdef bint separating_axis_many_c(list boxes1, list boxes2):
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
                if not separating_axis_c(box2,box1):
                    return 1
    return 0

cpdef bint separating_axis_many(list boxes1, list boxes2):
    return separating_axis_many_c(boxes1,boxes2)

cdef bint separating_axis_many_vs_1_c(bbox bb, list boxes):
    cdef int bcnt = len(boxes)



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
                if not separating_axis_c(box2,box1):
                    return 1
    return 0
'''#















