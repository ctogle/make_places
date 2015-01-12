import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.blueprints as mbp
import make_places.gritty as gritgeo

import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

import matplotlib.pyplot as plt

import pdb

class floor_sector(mbp.blueprint):
    # a sector is a convex 2d projection of a space to be stitched to other
    # sectors to form a building floor plan
    # should be able to fill a space as necessary
    # a building is made of references to a list of floor_plans
    # each floor is pointed to a single plan
    # the plans are a chosen to stack appropriately geometrically

    def __init__(self, *args, **kwargs):
        self._default_('fgaps',[],**kwargs)
        self._default_('cgaps',[],**kwargs)
        self._default_('shafted',False,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('ceiling_height',0.5,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        if kwargs.has_key('corners'):
            self.corners = kwargs['corners']
            c1,c3 = self.corners[0],self.corners[2]
            self.length = abs(c3.x - c1.x)
            self.width = abs(c3.y - c1.y)
            self.position = cv.center_of_mass(self.corners)
        else:
            l,w,p = kwargs['length'],kwargs['width'],kwargs['position']
            self.corners = mpu.make_corners(p,l,w,0)
            self.length = l
            self.width = w
            self.position = p
        self.set_bboxes() 

    def set_bboxes(self):
        com_vects = [
            cv.v1_v2(v,self.position).normalize().scale_u(0.5) 
                for v in self.corners]
        self.small_corners = [
            c.copy().translate(tv) for c,tv in 
                zip(self.corners,com_vects)]
        self.big_corners = [
            c.copy().translate(tv.flip()) for c,tv in 
                zip(self.corners,com_vects)]
        self.bboxes = [mpbb.bbox(corners = self.small_corners)]

    def get_bboxes(self):
        return self.bboxes

    def reducible(self,wpool):
        bwalls = self.find_walls(wpool)
        ibwalls = [w for w in bwalls if w.sort == 'interior']
        if self.fgaps: return False
        if len(ibwalls) == 1: return True
        else: return False
        #if len(bwalls) - len(ibwalls) > 3*len(ibwalls): return True

    def find_walls(self, wpool):
        mine = []
        for w in wpool:
            if cv.inside(w.v1,self.big_corners) and\
                    cv.inside(w.v2,self.big_corners):
                mine.append(w)
        self.bounding_walls = mine
        return mine

    def wall_verts(self):
        pairs = []
        ccnt = len(self.corners)
        for cdx in range(1,ccnt):
            c1,c2 = self.corners[cdx-1].copy(),self.corners[cdx].copy()
            #c1.translate_z(-0.5)
            #c2.translate_z(-0.5)
            pairs.append((c1,c2))
        c1,c2 = self.corners[-1].copy(),self.corners[0].copy()
        #c1.translate_z(-0.5)
        #c2.translate_z(-0.5)
        pairs.append((c1,c2))
        return pairs

    def build_lod(self,floor = True,ceiling = True):
        pieces = []
        fh = self.floor_height
        ch = self.ceiling_height
        wh = self.wall_height
        loff = wh + ch
        lheight = loff + fh
        piece = mbp.ucube()
        piece.is_lod = True
        #piece = pr.ucube(is_lod = True)
        piecenode = sg.node(
            position = self.position.copy().translate_z(-fh), 
            scales = cv.vector(self.length,self.width,wh+ch+fh), 
            lod_primitives = [piece])

        pieces.append(piecenode)
        #pieces.append(fl.floor(**largs))
        return pieces

    def build(self,hasfloor = True,hasceiling = True):
        #print 'BUILD FLOOR SECTOR!'

        if not hasfloor and not hasceiling: return []
        final = pr.empty_primitive()
        if hasfloor:
            if self.fgaps: fgap = self.fgaps[0]
            else: fgap = None
            fopts = {
                'gap':fgap,
                'l':self.length,
                'w':self.width,
                'h':self.floor_height,
                    }
            afloor = build_floor(**fopts)
            final.consume(afloor)
        if hasceiling:
            if self.cgaps: cgap = self.cgaps[0]
            else: cgap = None
            copts = {
                'gap':cgap,
                'l':self.length,
                'w':self.width,
                'h':self.floor_height,
                    }
            aceiling = build_floor(**copts)
            coff = self.ceiling_height + self.wall_height
            aceiling.translate_z(coff)
            final.consume(aceiling)

        piecenode = sg.node(
            position = self.position.copy(),
            primitives = [final])
        return [piecenode]

_floor_count_ = 0
class floorold(sg.node):

    def get_name(self):
        global _floor_count_
        nam = 'floor ' + str(_floor_count_)
        _floor_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self.seg_numbers = [str(x) for x in range(10)]  
        self._default_('name',self.get_name(),**kwargs)
        self._default_('length',20,**kwargs)
        self._default_('width',20,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('gaps',[],**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self.primitives = self.make_primitives(
            self.length,self.width,self.floor_height,self.gaps)
        sg.node.__init__(self, *args, **kwargs)

    def find_corners(self, length, width):
        x = length/2.0
        y = width/2.0
        pos = cv.vector(0,0,0)
        #c1 = mpu.translate_vector(pos.copy(),[-x,-y,0])
        #c2 = mpu.translate_vector(pos.copy(),[x,-y,0])
        #c3 = mpu.translate_vector(pos.copy(),[x,y,0])
        c1 = pos.copy().translate_x(-x).translate_y(-y)
        c2 = pos.copy().translate_x( x).translate_y(-y)
        c3 = pos.copy().translate_x( x).translate_y( y)
        c4 = pos.copy().translate_x(-x).translate_y( y)
        corners = [c1, c2, c3, c4]
        ttf = self.tform
        #ttf = self.tform.true()
        cv.rotate_z_coords(corners, ttf.rotation.z)
        cv.translate_coords(corners, ttf.position)
        return corners

    def make_primitives(self, length, width, flheight, gaps = []):
        self.corners = self.find_corners(length, width)
        pos = cv.vector(0,0,0)
        if len(gaps) == 0:
            self.gapped = False
            return self.make_floor_segment(
                pos, length, width, flheight)
        elif len(gaps) == 1:
            self.gapped = True
            gap = gaps[0]
            segments = []
            args = self.segment_single_projection_x(
                pos, length, width, flheight, gap)
            for ag in args:
                segments.extend(self.make_floor_segment(*ag))
            return segments
        else: print('failed to make a floor!!')

    def segment_single_projection_x(self, p, l, w, h, g):
        sargs = []
        c1x = p.x
        c1y = p.y
        c1z = p.z
        c2x = g[0].x
        c2y = g[0].y
        c2z = g[0].z
        lg = g[1]
        wg = g[2]
        s1l = l/2.0 + c2x - c1x - lg/2.0
        s1x = c1x - l/2.0 + s1l/2.0
        s1y = c1y
        s1z = c1z
        s2l = l - lg - s1l
        s2x = c2x + lg/2.0 + s2l/2.0
        s2y = c1y
        s2z = c1z
        s1 = (cv.vector(s1x,s1y,s1z),s1l,w,h)
        s2 = (cv.vector(s2x,s2y,s2z),s2l,w,h)
        s3w = w/2.0 + c2y - c1y - wg/2.0
        s3x = c2x
        s3y = c1y - w/2.0 + s3w/2.0
        s3z = c1z
        s4w = w - wg - s3w
        s4x = c2x
        s4y = c1y + wg/2.0 + s3w/2.0
        s4z = c1z
        s3 = (cv.vector(s3x,s3y,s3z),lg,s3w,h)
        s4 = (cv.vector(s4x,s4y,s4z),lg,s4w,h)
        return [s1,s2,s3,s4]

    def seg_number(self):
        if self.seg_numbers:return self.seg_numbers.pop(0)

    def make_floor_segment(self, pos, length, width, flheight):
        segnum = self.seg_number()
        #fl = unit_cube(tag = '_floor_segment_' + segnum)
        fl = mbp.ucube()
        fl.tag = '_floor_segment_' + segnum
        fl.scale(cv.vector(length, width, flheight))
        fl.translate(cv.vector(pos.x,pos.y,pos.z-flheight))
        return [fl]

class newfloor(mbp.blueprint):

    def __init__(self,l = 10,w = 10,h = 1,gap = None):
        mbp.blueprint.__init__(self)
        self.l = l
        self.w = w
        self.h = h
        self.gap = gap

    def _build_gap(self):
        l,w,h,g = self.l,self.w,self.h,self.gap
        gp,gl,gw = g
        iloop = mpu.make_corners(gp,gl,gw,0)
        oloop = mpu.make_corners(cv.zero(),l,w,0)
        iloop.append(iloop[0])
        oloop.append(oloop[0])

        newfaces = self._bridge(iloop,oloop)
        self._project_uv_xy(newfaces)

        iloopb = [c.copy() for c in iloop]
        oloopb = [c.copy() for c in oloop]
        [c.translate_z(-h) for c in iloopb]
        [c.translate_z(-h) for c in oloopb]

        newfaces = self._bridge(oloopb,iloopb)
        self._project_uv_xy(newfaces)

        newfaces = self._bridge(iloopb,iloop)

    def _build_nogap(self):
        l,w,h = self.l,self.w,self.h
        corners = mpu.make_corners(cv.zero(),l,w,0)
        us = mbp.polygon(4)
        cv.translate_coords(us,cv.one().scale_u(0.5))
        cv.scale_coords_x(us,l)
        cv.scale_coords_y(us,w)
        self._quad(*corners,us = us)
        [c.translate_z(-h) for c in corners]
        corners.reverse()
        self._quad(*corners,us = us)

    def _build(self):
        if self.gap is None: self._build_nogap()
        else: self._build_gap()

floor_factory = newfloor()
floor_factory._build()
def build_floor(**opts):
    floor_factory._rebuild(**opts)
    return floor_factory._primitive_from_slice()
    
def test_floor_factory():
    fopts = {'l':20,'w':30,'h':0.5,'gap':(cv.zero(),10,10)}
    afloor = build_floor(**fopts)
    gritgeo.create_primitive(afloor)








