import make_places.fundamental as fu
from make_places.fundamental import element
from make_places.primitives import unit_cube

import numpy as np

class wall(element):

    def __init__(self, *args, **kwargs):
        self.v1 = args[0]
        self.v2 = args[1]
        v1, v2 = self.v1, self.v2
        self.v1_v2 = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
        try: self.length = kwargs['length']
        except KeyError: self.length = fu.magnitude(self.v1_v2)
        try: self.width = kwargs['wall_width']
        except KeyError: self.width = 0.4
        try: self.height = kwargs['wall_height']
        except KeyError: self.height = 4
        try: self.gaps = kwargs['wall_gaps']
        except KeyError: self.gaps = []
        try:
            if kwargs['gaped']:
                self.gaps = self.gape_wall()
        except KeyError: pass
        kwargs['primitives'] = self.make_primitives(
            self.v1, self.v1, self.v2, self.gaps)
        pos = self.v1[:]
        kwargs['position'] = pos
        element.__init__(self, *args, **kwargs)

    def gape_wall(self):
        wlen = float(self.length)
        gwid = 4.0
        gcnt = int(wlen/(gwid*2))
        gaps = []
        if gcnt > 0: gspa = wlen/gcnt
        for gn in range(gcnt):
            gp = (gn + 0.5)*gspa - gwid/2.0
            gaps.append((gp,gwid))
        return gaps

    def make_wall_segment(self, pos, v1, v2):
        wall_ = unit_cube()
        length = fu.distance_xy(v1,v2)
        wall_.scale([length, self.width, self.height])
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
            #spos = [fr[0]-v1[0],fr[1]-v1[1],fr[2]-v1[2]]
            spos = fu.v1_v2(v1,fr)
            wall_ = self.make_wall_segment(spos, fr, bk)
            prims.append(wall_)
        return prims

class perimeter(element):

    def __init__(self, *args, **kwargs):
        try:
            self.floor = kwargs['floor']
            corners = self.floor.corners
        except KeyError: corners = kwargs['corners']
        try: self.width = kwargs['wall_width']
        except KeyError: self.width = 0.4
        try: self.height = kwargs['wall_height']
        except KeyError: self.height = 4
        try: self.gaps = kwargs['wall_gaps']
        except KeyError: self.gaps = [[],[],[],[]]
        try: self.gaped = kwargs['gaped']
        except KeyError: self.gaped = False
        self.gapes = [self.gaped]*len(self.gaps)
        kwargs['children'] = self.make_walls(corners, 
            gapes = self.gapes, gaps = self.gaps)
        element.__init__(self, *args, **kwargs)

    def make_walls(self, corners, 
            gapes = [True,True,False,False], 
            gaps = [[],[],[],[]]):
        walls = []
        c1 = corners[0]
        c2 = corners[1]
        c3 = corners[2]
        c4 = corners[3]
        ww = self.width
        h = self.height
        walls.append(wall(c1, c2, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[0], gaped = gapes[0]))
        walls.append(wall(c2, c3, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[1], gaped = gapes[1]))
        walls.append(wall(c3, c4, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[2], gaped = gapes[2]))
        walls.append(wall(c4, c1, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[3], gaped = gapes[3]))
        return walls






