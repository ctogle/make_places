#imports
# cython: profile=True
#cimport cython
from libc.math cimport sqrt

import mp_vector as cv
cimport mp_vector as cv

import matplotlib.pyplot as plt

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

cdef list intersection_c(bb1,bb2):
    # should return the set of intersection points
    # between 2 bboxes

    cdef list ns1 = bb1.edgenorms
    cdef list ns2 = bb2.edgenorms
    cdef int egcnt1 = bb1.edgecount
    cdef int egcnt2 = bb2.edgecount
    cdef cv.vector edgenorm
    cdef int egdx
    cdef cv.vector2d proj1
    cdef cv.vector2d proj2

    cdef list ipts = []

    for egdx in range(egcnt1):
        edgenorm = <cv.vector>ns1[egdx]
        proj1 = <cv.vector2d>project_c(bb1.corners,edgenorm)
        proj2 = <cv.vector2d>project_c(bb2.corners,edgenorm)
        if not <bint>overlap_c(proj1,proj2):
            return ipts
    for egdx in range(egcnt2):
        edgenorm = <cv.vector>ns2[egdx]
        proj1 = <cv.vector2d>project_c(bb1.corners,edgenorm)
        proj2 = <cv.vector2d>project_c(bb2.corners,edgenorm)
        if not <bint>overlap_c(proj1,proj2):
            return ipts
    return ipts

cpdef list intersection(bb1,bb2):
    return intersection_c(bb1,bb2)

cdef float distance_to_border_c(cv.vector pt, list border):
    edgenorms = get_norms_c(border)
    dists = []
    for edx in range(len(border)):
        e1 = border[edx-1]
        e2 = border[edx]
        norm = edgenorms[edx-1]
        dists.append(distance_to_edge(pt,e1,e2,norm))
    dists.append(dists.pop(0))
    distance = min(dists)
    return distance

cpdef float distance_to_border(cv.vector pt, list border):
    return distance_to_border_c(pt,border)

cdef float distance_to_edge_c(cv.vector pt,
        cv.vector e1,cv.vector e2,cv.vector nm):
    print 'not implemented'
    eproj = project([e1,e2],nm)
    pproj = project([pt],nm)
    return abs(eproj.x - pproj.x)

cpdef float distance_to_edge(cv.vector pt,
        cv.vector e1,cv.vector e2,cv.vector nm):
    return distance_to_edge_c(pt,e1,e2,nm)

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
    for vdx in range(vcnt):
        v1,v2 = verts[vdx-1],verts[vdx]
        dx = v2.x - v1.x
        dy = v2.y - v1.y
        dv = sqrt(dx**2 + dy**2)
        #if dv == 0.0:
        #    print 'dv',dv,dx,dy
        #    print v1,v2
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

cpdef bint intersect_xy(bbox bb1, bbox bb2):
    cdef float br1 = bb1.radius
    cdef float br2 = bb2.radius
    bbdist = cv.distance_xy_c(bb1.center,bb2.center)
    if bbdist <= br1 + br2:
        if not separating_axis(bb1,bb2):
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

    def __str__(self):
        strr = 'bbox with corners:\n'
        for c in self.corners:
            strr += '\t' + c.__str__()
        return strr






def xy_projection(verts):
    xproj = project(verts,cv.xhat)
    yproj = project(verts,cv.yhat)
    c1 = cv.vector(xproj.x,yproj.x,0)
    c2 = cv.vector(xproj.y,yproj.x,0)
    c3 = cv.vector(xproj.y,yproj.y,0)
    c4 = cv.vector(xproj.x,yproj.y,0)
    return [c1,c2,c3,c4]

def inscribe(subjects):
    subjcorners = []
    for subj in subjects:
        subjcorners.extend(subj.corners)
    return xy_projection(subjcorners)

cdef class xy_bbox:
    cdef public xy_bbox parent
    cdef public bbox bb
    cdef public object owner
    cdef public list children
    cdef public list corners
    cdef public list edgenorms
    cdef public int edgecount
    cdef public float radius
    cdef public cv.vector center

    cdef public int segment_id
    cdef public bint bottomlevel

    # this is temporary!
    def copy(self):
        return bbox(corners = self.corners)

    def intersect_xy(self, other, info = None):
        if info is None:
            info = {
                'self':self,
                'other':other, 
                'self members':[], 
                'other members':[], 
                'center':None, 
                    }
        #if intersect_xy(self.copy(),other.copy()):
        if intersect_xy(self.bb,other.bb):
            if self.children and not other.children:
                children_isect = False
                subcenters = []
                for ch in self.children:
                    chiinfo = self.intersect_xy(ch,info = info)
                    if not chiinfo is None:
                        children_isect = True
                        subcenters.append(chiinfo['center'])
                        for sm in chiinfo['self members']:
                            if not sm in info['self members']:
                                info['self members'].append(sm)
                        for osm in chiinfo['other members']:
                            if not osm in info['other members']:
                                info['other members'].append(osm)
                if children_isect:
                    info['center'] = cv.com(subcenters)
                    return info
                else: return None
            elif not self.children and other.children:
                children_isect = False
                subcenters = []
                for och in other.children:
                    chiinfo = self.intersect_xy(och,info = info)
                    if not chiinfo is None:
                        children_isect = True
                        subcenters.append(chiinfo['center'])
                        for sm in chiinfo['self members']:
                            if not sm in info['self members']:
                                info['self members'].append(sm)
                        for osm in chiinfo['other members']:
                            if not osm in info['other members']:
                                info['other members'].append(osm)
                if children_isect:
                    info['center'] = cv.com(subcenters)
                    return info
                else: return None
            elif self.children and other.children:
                children_isect = False
                subcenters = []
                for ch in self.children:
                    for och in other.children:
                        chiinfo = ch.intersect_xy(och,info = info)
                        if not chiinfo is None:
                            children_isect = True
                            subcenters.append(chiinfo['center'])
                            for sm in chiinfo['self members']:
                                if not sm in info['self members']:
                                    info['self members'].append(sm)
                            for osm in chiinfo['other members']:
                                if not osm in info['other members']:
                                    info['other members'].append(osm)
                if children_isect:
                    info['center'] = cv.com(subcenters)
                    return info
                else: return None
            else:
                info['self members'].append(self)
                info['other members'].append(other)
                info['center'] = cv.midpoint(self.center,other.center)
                return info
        else: return None

    def plot_corners(self, color = 'black'):
        x = [c.x for c in self.corners]
        y = [c.y for c in self.corners]
        x.append(x[0])
        y.append(y[0])
        plt.plot(x,y,color = color,marker = 'o')

    def plot(self, colors = None):
        if colors is None:
            colors = ['black','red','green','blue','purple']
        color = colors.pop(0)
        self.plot_corners(color)
        for ch in self.children:
            ch.plot(colors[:])

    def __init__(self,corners = None,children = None,owner = None):
        # bboxes are always in world coords
        # either pass in corners or children or both
        self.owner = owner
        self.parent = self
        self.children = []
        if not children is None:
            self.bottomlevel = False
            for ch in children:
                self.add_child(ch)
            if corners is None:
                corners = self.project_children()
        else: self.bottomlevel = True

        self.corners = corners
        self.edgenorms = get_norms_c(self.corners)
        self.edgecount = len(self.edgenorms)
        self.center = cv.com(self.corners)
        cvs = [cv.v1_v2_c(self.center,v) for v in self.corners]
        cdists = [c.magnitude() for c in cvs]
        self.radius = max(cdists)

        self.bb = self.copy()

    def project_children(self):
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

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def __str__(self):
        strr = 'bbox with corners:\n'
        for c in self.corners:
            strr += '\t' + c.__str__()
        return strr

def test_new_bb():
    print 'test!'











