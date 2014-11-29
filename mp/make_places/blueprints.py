#import make_places.scenegraph as sg
import make_places.fundamental as fu
import make_places.walls as wa
#import make_places.primitives as pr
import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

#from make_places.stairs import ramp
#from make_places.stairs import shaft
#from make_places.floors import floor
#from make_places.walls import wall
#from make_places.walls import perimeter

from math import cos
from math import sin
from math import tan
from math import sqrt
import numpy as np
import random as rm
import pdb

class blueprint(fu.base):
    def __init__(self, *args, **kwargs):
        pass

class door_plan(blueprint):
    def __init__(self, position, **kwargs):
        self.position = position
        self._default_('width',1,**kwargs)
        self._default_('height',3,**kwargs)

class window_plan(blueprint):
    def __init__(self, position, **kwargs):
        self.position = position
        self._default_('width',1,**kwargs)
        self._default_('height',2,**kwargs)
        self._default_('zoffset',1,**kwargs)


    

def circumscribe_box(corners,outline):
    # move any vertex outside of corners to the nearest edge
    #
    c1,c2,c3,c4 = corners
    l = c2.x - c1.x
    w = c4.y - c1.y
    print 'totally unfinished'

# walk_line makes an xy outline of a building
def walk_line(corners):
    c1,c2,c3,c4 = corners
    l = c2.x - c1.x
    w = c4.y - c1.y
    steps = rm.choice([4,5,6,8])
    angle = 360.0/steps
    turns = [x*angle for x in range(steps)]
    stepl = 0.8*min([l,w])
    lengs = [stepl]*steps
    start = corners[0].copy()
    start.translate(cv.vector(l/10.0,w/10.0,0))
    outline = [start]
    newz = start.z
    current_angle = 0.0
    for dex in range(steps-1):
        l,t = lengs[dex],turns[dex]
        current_angle = t
        dx = l*cos(fu.to_rad(current_angle))
        dy = l*sin(fu.to_rad(current_angle))
        #quadr = fu.quadrant(fu.to_rad(current_angle))
        #dxsign = 1.0 if quadr in [1,4] else -1.0
        #dysign = 1.0 if quadr in [1,2] else -1.0
        dxsign = 1.0
        dysign = 1.0
        last = outline[-1]
        newx = last.x + dx*dxsign
        newy = last.y + dy*dysign
        new = cv.vector(newx,newy,newz)
        outline.append(new)
    return circumscribe_box(corners,outline)

def outline_test(center):
    c1 = cv.vector(-10,-10,0)
    c2 = cv.vector( 10,-10,0)
    c3 = cv.vector( 10, 10,0)
    c4 = cv.vector(-10, 10,0)
    corners = [c1,c2,c3,c4]
    cv.translate_coords(corners,center)
    outy = walk_line(corners)
    return outy






class floor_sector(blueprint):
    # a sector is a convex 2d projection of a space to be stitched to other
    # sectors to form a building floor plan
    # should be able to fill a space as necessary
    # a building is made of references to a list of floor_plans
    # each floor is pointed to a single plan
    # the plans are a chosen to stack appropriately geometrically

    def __init__(self, *args, **kwargs):
        self.corners = kwargs['corners']
        self.sides = range(len(self.corners))
        self.side_count = len(self.sides)
        self._default_('doorways',[],**kwargs)
        blueprint.__init__(self, *args, **kwargs)

    def build(self):
        print 'BUILD FLOOR SECTOR!'
        pieces = []
        rid = False
        ww = 0.5
        h = 4.0
        wargs = {
            'rid_top_bottom':rid,
            'wall_width':ww, 
            'wall_height':h, 
            'gaped':False, 
                }
        ccnt = len(self.corners)
        for c in range(1,ccnt):
            c1 = self.corners[c-1]
            c2 = self.corners[c]
            pieces.append(wa.wall(c1,c2,**wargs))
        c1,c2 = self.corners[-1],self.corners[0]
        pieces.append(wall(c1,c2,**wargs))

        for dw in self.doorways: print dw

        return pieces

    def grow(self):
        side = rm.choice(self.sides)
        d1 = side + 1 if side < self.side_count - 1 else 0
        d2 = side
        c1 = self.corners[d1]
        c2 = self.corners[d2]
        c3,c4 = self.extrude(c1,c2)
        dpos = cv.midpoint(c1,c2)
        dangz = cv.angle_from_xaxis_xy(self.c1c2)
        newcorners = [c1,c2,c3,c4]
        newdoorways = [door_plan(position = dpos,orientation = dangz)]
        sect = floor_sector(
            corners = newcorners,
            doorways = newdoorways)
        return sect

    def extrude(self,c1,c2):
        c1c2 = cv.v1_v2(c1,c2)
        c1c2n = cv.cross(fu.zhat,c1c2).normalize()
        eleng = rm.choice([3,4,5])
        c1c2n.scale(cv.vector(eleng,eleng,eleng))
        c3 = c2.copy().translate(c1c2n)
        c4 = c1.copy().translate(c1c2n)
        self.c1c2 = c1c2
        self.c1c2n = c1c2n
        return c3,c4
        
        

        

class floor_plan(blueprint):
    # a floor_plan should generate all parameters necessary to make a building
    #
    def __init__(self, *args, **kwargs):
        self._default_('length',10,**kwargs)
        self._default_('width',10,**kwargs)
        self._default_('entrance',0,**kwargs)
        self.sectors = self.divide_space()

    def build(self):
        for sector in self.sectors: sector.build()

    def main_space(self):
        l,w = self.length,self.width
        sub_length = rm.choice([0.5*l,0.75*l,l])
        sub_width = rm.choice([0.5*w,0.75*w,w])
        c1 = cv.vector(0,0,0)
        c2 = cv.vector(sub_length,0,0)
        c3 = cv.vector(sub_length,sub_width,0)
        c4 = cv.vector(0,sub_width,0)
        corners = [c1,c2,c3,c4]
        if self.entrance == 0:
            # south side should be flush
            offset = cv.vector(0,0,0)
            [c.translate(offset) for c in corners]
            dpos = cv.midpoint(c1,c2)
            dangz = 0.0
            doorways = [door_plan(position = dpos,orientation = dangz)]
        else:
            print 'nonzero entrance value non implemented!'

        sect = floor_sector(corners = corners,doorways = doorways)
        #self.doorways = doorways
        self.front_door = doorways[0]
        return sect

    def divide_space(self):
        sections = rm.choice([1,2,3])
        sectors = [self.main_space()]
        for sect in range(sections):
            sectors.append(sectors[-1].grow())
            print sect
        return sectors

def test_bp():
    bp = floor_plan()
    bp.build()

















