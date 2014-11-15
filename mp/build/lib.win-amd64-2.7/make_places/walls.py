import make_places.fundamental as fu
#from make_places.fundamental import element
from make_places.scenegraph import node
import make_places.scenegraph as scg
from make_places.primitives import unit_cube

import numpy as np

class wall(node):

    def __init__(self, *args, **kwargs):
        self.v1 = args[0]
        self.v2 = args[1]
        v1, v2 = self.v1, self.v2
        self.v1_v2 = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
        self._default_('length',fu.distance(v1,v2),**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('wall_height',4,**kwargs)
        self._default_('gaps',[],**kwargs)
        try:
            if kwargs['gaped']:
                self.gaps = self.gape_wall()
        except KeyError: pass
        kwargs['primitives'] = self.make_primitives(
            self.v1, self.v1, self.v2, self.gaps)
        pos = self.v1[:]
        kwargs['position'] = pos
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        #tform = scg.tform(position = pos)
        #self._default_('tform',tform,**kwargs)
        node.__init__(self, *args, **kwargs)

    def gape_wall(self):
        wlen = float(self.length)
        gwid = 4.0
        #gcnt = int(wlen/(gwid*2))
        gcnt = 1 if wlen > gwid*2 else 0
        gaps = []
        if gcnt > 0: gspa = wlen/gcnt
        for gn in range(gcnt):
            gp = (gn + 0.5)*gspa - gwid/2.0
            gaps.append((gp,gwid))
        return gaps

    def make_wall_segment(self, pos, v1, v2):
        wall_ = unit_cube()
        length = fu.distance_xy(v1,v2)
        wall_.scale([length, self.wall_width, self.wall_height])
        wall_.translate([length/2.0,0,0])
        ang_z = fu.angle_from_xaxis_xy(fu.v1_v2(v1,v2))
        wall_.rotate_z(ang_z)
        if fu.magnitude(pos) > 0: wall_.translate(pos)
        return wall_

    def make_primitives(self, pos, v1, v2, gaps = []):
        tang = fu.normalize([v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]])
        segmented = [v1, v2]
        for gap in gaps:
            cent = gap[0]
            widt = gap[1]
            nv1 = v1[:]
            fu.translate_vector(nv1, [t*cent for t in tang])
            nv2 = nv1[:]
            fu.translate_vector(nv2, [t*widt for t in tang])
            newvs = [nv1, nv2]
            segmented.extend(newvs)
            segmented.append(segmented.pop(-3))
        frnts = segmented[::2]
        backs = segmented[1::2]
        prims = []
        for sgdx in range(len(frnts)):
            fr = frnts[sgdx]
            bk = backs[sgdx]
            spos = fu.v1_v2(v1,fr)
            wall_ = self.make_wall_segment(spos, fr, bk)
            prims.append(wall_)
        return prims

class perimeter(node):

    def __init__(self, *args, **kwargs):
        self._default_('wall_offset',0,**kwargs)
        self._default_('floor',None,**kwargs)
        if self.floor: corns = self.floor.corners
        else: corns = kwargs['corners']
        corns = self.add_corner_offset(corns)
        self._default_('corners',corns,**kwargs)
        self._default_('wall_width', 0.4, **kwargs)
        self._default_('wall_height', 4, **kwargs)
        self._default_('wall_gaps',[[],[],[],[]],**kwargs) 
        self._default_('gaped',False,**kwargs)
        self.gapes = [self.gaped]*len(self.wall_gaps)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('children',self.make_walls(
            self.corners,gapes = self.gapes,
                gaps = self.wall_gaps), **kwargs)
        node.__init__(self, *args, **kwargs)

    def add_corner_offset(self, cns):
        off = -self.wall_offset
        cns[0][0] += off
        cns[0][1] += off
        cns[1][0] -= off
        cns[1][1] += off
        cns[2][0] -= off
        cns[2][1] -= off
        cns[3][0] += off
        cns[3][1] -= off
        return cns

    def make_walls(self, corners, 
            gapes = [True,True,False,False], 
            gaps = [[],[],[],[]]):
        walls = []
        c1 = corners[0]
        c2 = corners[1]
        c3 = corners[2]
        c4 = corners[3]
        ww = self.wall_width
        h = self.wall_height
        walls.append(wall(c1, c2, parent = self, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[0], gaped = gapes[0]))
        walls.append(wall(c2, c3, parent = self, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[1], gaped = gapes[1]))
        walls.append(wall(c3, c4, parent = self, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[2], gaped = gapes[2]))
        walls.append(wall(c4, c1, parent = self, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[3], gaped = gapes[3]))
        return walls






