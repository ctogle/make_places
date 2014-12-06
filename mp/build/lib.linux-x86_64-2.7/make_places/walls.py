import make_places.fundamental as fu
#from make_places.fundamental import element
from make_places.scenegraph import node
import make_places.scenegraph as scg
import make_places.primitives as pr
from make_places.primitives import unit_cube
import mp_utils as mpu
import mp_vector as cv

import numpy as np

_wall_count_ = 0
class wall(node):

    def get_name(self):
        global _wall_count_
        nam = 'wall ' + str(_wall_count_)
        _wall_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self.v1 = args[0]
        self.v2 = args[1]
        v1, v2 = self.v1, self.v2
        #self.v1_v2 = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
        self.v1_v2 = cv.v1_v2(v1,v2)
        self.angle = cv.angle_from_xaxis_xy(self.v1_v2)
        self._default_('rid_top_bottom',True,**kwargs)
        self._default_('length',cv.distance(v1,v2),**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('wall_height',4,**kwargs)
        self._default_('gaps',[],**kwargs)
        try:
            if kwargs['gaped']:
                self.gaps = self.gape_wall()
        except KeyError: pass
        kwargs['primitives'] = self.make_primitives(
            self.v1, self.v1, self.v2, self.gaps)
        pos = self.v1.copy()
        kwargs['position'] = pos
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        node.__init__(self, *args, **kwargs)

    def gape_wall(self):
        wlen = float(self.length)
        gwid = 4.0
        gcnt = int(wlen/(gwid*2))
        #gcnt = 1 if wlen > gwid*2 else 0
        gaps = []
        if gcnt > 0: gspa = wlen/gcnt
        for gn in range(gcnt):
            gp = (gn + 0.5)*gspa - gwid/2.0
            gaps.append((gp,gwid))
        return gaps

    def make_wall_segment(self, pos, v1, v2, wall_scales):
        wall_ = unit_cube()
        if self.rid_top_bottom:
            wall_.remove_face('top','bottom')
        length = cv.distance_xy(v1,v2)
        wall_.scale(cv.vector(length, self.wall_width, self.wall_height))
        wall_.translate_x(length/2.0)
        wall_.rotate_z(self.angle)
        wall_.translate(pos)
        return wall_

    def make_primitives(self, pos, v1, v2, gaps = []):
        tang = self.v1_v2.copy().normalize()
        segmented = [v1, v2]
        wlength = cv.distance(v1,v2)
        wscls = cv.vector(wlength, self.wall_width, self.wall_height)
        for gap in gaps:
            cent = gap[0]
            #cent = gap[0]*wlength - 0.5*gap[1]

            widt = gap[1]
            nv1 = v1.copy()
            # start here
            nv1.translate(tang.copy().scale_u(cent))
            #cv.translate_vector(nv1, [t*cent for t in tang])
            nv2 = nv1.copy()
            nv2.translate(tang.copy().scale_u(widt))
            #mpu.translate_vector(nv2, [t*widt for t in tang])
            newvs = [nv1, nv2]
            segmented.extend(newvs)
            segmented.append(segmented.pop(-3))

        frnts = segmented[::2]
        backs = segmented[1::2]
        prims = []
        for sgdx in range(len(frnts)):
            fr = frnts[sgdx]
            bk = backs[sgdx]
            spos = cv.v1_v2(v1,fr)
            wall_ = self.make_wall_segment(spos, fr, bk, wscls)
            prims.append(wall_)
        return prims

_perim_count_ = 0
class perimeter(node):
    
    def get_name(self):
        global _perim_count_
        nam = 'perimeter ' + str(_perim_count_)
        _perim_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self._default_('name',self.get_name(),**kwargs)
        self._default_('floor',None,**kwargs)
        if self.floor: corns = self.floor.corners
        else: corns = kwargs['corners']
        self._default_('wall_offset',0,**kwargs)
        self._default_('rid_top_bottom_walls',True,**kwargs)
        corns = self.add_corner_offset(corns)
        self._default_('corners',corns,**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('wall_width', 0.5, **kwargs)
        self._default_('wall_height', 4, **kwargs)
        self._default_('wall_gaps',[[],[],[],[]],**kwargs) 
        self._default_('gaped',True,**kwargs)
        self.gapes = [self.gaped]*len(self.wall_gaps)
        self.add_child(*self.make_walls(self.corners,
            gapes = self.gapes,gaps = self.wall_gaps))
        node.__init__(self, *args, **kwargs)

    def add_corner_offset(self, cns):
        off = -self.wall_offset
        cns[0].x += off
        cns[0].y += off
        cns[1].x -= off
        cns[1].y += off
        cns[2].x -= off
        cns[2].y -= off
        cns[3].x += off
        cns[3].y -= off
        return cns

    def make_walls(self, corners, 
            gapes = [True,True,False,False], 
            gaps = [[],[],[],[]]):
        rid = self.rid_top_bottom_walls
        walls = []

        gcnt = len(gaps)
        ccnt = len(corners)
        if gcnt < ccnt:
            gaps.extend([[]]*(ccnt-gcnt))
            gapes.extend([False]*(ccnt-gcnt))

        ww = self.wall_width
        h = self.wall_height
        for cdx in range(1,ccnt):
            c1,c2 = corners[cdx-1],corners[cdx]
            walls.append(wall(c1, c2, rid_top_bottom = rid, 
                wall_width = ww, wall_height = h, 
                wall_gaps = gaps[cdx-1], gaped = gapes[cdx-1]))

        c1,c2 = corners[-1],corners[0]
        walls.append(wall(c1, c2, rid_top_bottom = rid, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[cdx], gaped = gapes[cdx]))
        return walls


      






