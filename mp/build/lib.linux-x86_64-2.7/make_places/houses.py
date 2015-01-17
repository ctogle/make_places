import make_places.fundamental as fu
import make_places.scenegraph as sg
import make_places.primitives as pr
import make_places.materials as mpm
import make_places.blueprints as mbp

import make_places.floors as fl
import make_places.walls as wa
import make_places.portals as po

import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

import matplotlib.pyplot as plt

class room(mbp.blueprint):
    
    def _plot(self):
        mbp.plot(self.corners,color = 'red',marker = 's')

    def __init__(self,corners = None,
            h = 4,fh = 0.5,ch = 0.5,
            fm = 'asphalt',cm = 'glass'):
        mbp.blueprint.__init__(self)
        if corners is None:
            corners = mpu.make_corners(cv.zero(),10,10,0)
        self.corners = corners
        self.h = h
        self.fh = fh
        self.ch = ch
        self.fm = fm
        self.cm = cm
        
        self.enorms = mpbb.get_norms(self.corners)
        self.center = cv.center_of_mass(self.corners)

    def _rebuild(self,**opts):
        mbp.blueprint._rebuild(self,**opts)
        self.enorms = mpbb.get_norms(self.corners)
        self.center = cv.center_of_mass(self.corners)

    def _build(self):
        h,bcorners = self.h,self.corners[:]

        self._build_floor(bcorners)
        self._build_ceiling(bcorners)

    def _build_floor(self,cs):
        fh,fm = self.fh,self.fm
        fcs = [c.copy().translate_z(fh) for c in cs]
        nfs = self._tripie(fcs,m = fm)
        self._project_uv_xy(nfs)

    def _build_ceiling(self,cs):
        h,fh,ch,cm = self.h,self.fh,self.ch,self.cm
        cz = h - ch
        ccs = [c.copy().translate_z(cz) for c in cs]
        ccs.reverse()
        nfs = self._tripie(ccs,m = cm)
        self._project_uv_xy(nfs)

    def _grow(self):
        print 'grow!'

room_factory = room()
room_factory._build()
def build_room(**opts):
    room_factory._rebuild(**opts)
    return room_factory._primitive_from_slice()

class house(mbp.blueprint):

    def _primitives(self):return self._children
    def __init__(self,l = 40,w = 60,stories = 2):
        mbp.blueprint.__init__(self)
        self.stories = stories
        self.l = l
        self.w = w

        p = cv.zero()
        self.lot = mpu.make_corners(p,self.l,self.w,0)

    def _build(self):
        self._children = []
        self._build_yard()
        for sx in range(self.stories):
            self._build_story(sx)
        self._build_roof()
        self._children.append(self._primitive_from_slice())
        print 'built house!'

    def _build_yard(self):
        corners = self.lot
        yfaces = self._quad(*corners,m = 'grass2')
        self._project_uv_xy(yfaces)

    def _build_story(self,sdx):
        self._build_rooms(sdx)

    def _build_main_room(self,story):
        ml,mw = 8,10
        mcs = mpu.make_corners(cv.zero(),ml,mw,0)

        fh,ch,wh,ww = self._params()
        mroom,mwalls = self._build_room(mcs,fh,ch,wh,ww)
        if story == 0:
            entrance = mwalls[0]
            entrance._door_gap(0.5,fh)

        self.rooms = [mroom]
        self.walls = mwalls

    def _build_room(self,corners,fh,ch,wh,ww):
        def wall_verts(mcs):
            pairs = []
            for x in range(len(mcs)):
                pairs.append((mcs[x-1],mcs[x]))
            return pairs

        rcorners = [c.copy() for c in corners]
        nroom = {'corners':rcorners,'fh':fh,'ch':ch,'h':wh}
        nroom = room(**nroom)
        nwals = [{'v1':v1,'v2':v2,'sort':'exterior',
                    'sector':nroom,'h':wh,'fh':fh,'w':ww} 
                for v1,v2 in wall_verts(corners)]
        nwals = [wa.newwall(**wo) for wo in nwals]
        return nroom,nwals

    def _build_rooms(self,story = 0):
        self._build_main_room(story)

        #gws = 5
        #for g in range(gws):self._grow()
        bw = self.walls[-2]
        self._extrude(bw,10)

        bw = self.walls[-2]
        self._extrude(bw,10)

        bw = self.walls[-2]
        self._extrude(bw,20)

        self._construct(self.rooms,story)
        self._construct(self.walls,story)

    def _build_roof(self):
        fh,ch,wh,ww = self._params()
        rh = wh*self.stories
        for r in self.rooms:
            rc = [c.copy().translate_z(rh) for c in r.corners]
            mbp.inflate(rc,ww)
            nfs = self._quad(*rc,m = 'metal')
            self._project_uv_flat(nfs)

    def _construct(self,bps,story):
        fh,ch,wh,ww = self._params()
        sh = wh*story
        for bp in bps:
            bp._build()
            p = bp._primitive_from_slice()
            if not sh == 0.0:p.translate_z(sh)
            for sp in bp._extra_primitives:
                if not sh == 0.0:sp.translate_z(sh)
                p.consume(sp)
            self._children.append(p)

    def _plot(self):
        for r in self.rooms:r._plot()
        for w in self.walls:w._plot()

    def _params(self):
        fh,ch,wh,ww = 0.25,0.25,4,0.25
        return fh,ch,wh,ww

    def _extrude(self,wall,el):
        wall._face_away()
        wall.sort = 'interior'
        e1,e2 = wall.v1.copy(),wall.v2.copy()
        e4,e3 = mbp.extrude_edge_normal(e2,e1,el)
        ncs = [e2,e1,e4,e3]

        fh,ch,wh,ww = self._params()
        nroom,nwalls = self._build_room(ncs,fh,ch,wh,ww)
        nwalls.pop(1)
        self.rooms.append(nroom)
        self.walls.extend(nwalls)

    def _grow(self):
        print 'grow!'

house_factory = house()
#house_factory._build()
def build_house(**opts):
    house_factory._rebuild(**opts)
    return house_factory._primitives()









