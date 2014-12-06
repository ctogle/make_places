import make_places.scenegraph as sg
import make_places.fundamental as fu
import make_places.walls as wa
import make_places.floors as fl
import make_places.stairs as st
#import make_places.primitives as pr
import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

#from make_places.stairs import ramp
#from make_places.stairs import shaft

from math import cos
from math import sin
from math import tan
from math import sqrt
import numpy as np
import random as rm
import pdb

def extrude_edge(c1,c2,length,direction):
    #c1c2 = cv.v1_v2(c1,c2)
    c1c2n = direction.normalize().scale_u(length)
    #c1c2n = cv.cross(cv.zhat,c1c2).normalize()
    #c1c2n.scale_u(length)
    c3 = c2.copy().translate(c1c2n)
    c4 = c1.copy().translate(c1c2n)
    return c3,c4

def extrude_edge_normal(c1,c2,length):
    c1c2 = cv.v1_v2(c1,c2)
    c1c2n = cv.cross(cv.zhat,c1c2)
    return extrude_edge(c1,c2,length,c1c2n)

class blueprint(fu.base):
    def __init__(self, *args, **kwargs):
        pass

class door_plan(blueprint):
    def __init__(self, position, rotation, **kwargs):
        self.position = position
        self.rotation = rotation
        self._default_('width',1,**kwargs)
        self._default_('height',3,**kwargs)

class window_plan(blueprint):
    def __init__(self, position, **kwargs):
        self.position = position
        self._default_('width',1,**kwargs)
        self._default_('height',2,**kwargs)
        self._default_('zoffset',1,**kwargs)

class shaft_plan(blueprint):
    def __init__(self, position, **kwargs):
        self.position = position
        self._default_('floors',3,**kwargs)
        self._default_('floor_heights',[0.5]*self.floors,**kwargs)
        self._default_('ceiling_heights',[0.5]*self.floors,**kwargs)
        self._default_('wall_heights',[4.0]*self.floors,**kwargs)
        #self._default_('floor_height',0.5,**kwargs)
        #self._default_('ceiling_height',0.5,**kwargs)
        #self._default_('wall_height',4.0,**kwargs)
        self._default_('length',8,**kwargs)
        self._default_('width',8,**kwargs)

    def build(self):
        pieces = []
        shargs = {
            'position':self.position, 
            'floor_heights':self.floor_heights, 
            'ceiling_heights':self.ceiling_heights, 
            'wall_heights':self.wall_heights, 
            'length':self.length, 
            'width':self.width, 
            'floors':self.floors, 
                }
        pieces.append(st.shaft(**shargs))
        return pieces

class wall_plan(blueprint):
    def __init__(self,v1,v2,sector = None,sort = 'exterior',**kwargs):
        self.sort = sort
        self.sector = sector
        self._default_('wall_width',0.5,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        self._default_('unswitchable',False,**kwargs)
        self.v1 = v1
        self.v2 = v2
        self.v1v2 = cv.v1_v2(v1,v2)
        self.lead_tip_rot = 0.0
        self.rear_tip_rot = 0.0
        self.length = self.v1v2.magnitude()
        self.normal = cv.cross(self.v1v2,cv.zhat).normalize()
        self.tangent = self.v1v2.copy().normalize()

    def face_away(self):
        intpt = self.sector.position
        midpt = cv.midpoint(self.v1,self.v2)
        tstpt = midpt.copy().translate(self.normal)
        if cv.distance(intpt,midpt) > cv.distance(intpt,tstpt):
            self.normal.flip()

        certain_tangent = cv.zhat.cross(self.normal)
        tstpt = midpt.copy().translate(certain_tangent)
        if cv.distance(self.v1,midpt) > cv.distance(self.v1,tstpt):
            v1 = self.v1
            self.v1 = self.v2
            self.v2 = v1
            self.v1v2 = cv.v1_v2(self.v1,self.v2)
            self.tangent = self.v1v2.copy().normalize()

    def fill_windows(self, windows):

        def _____clamp(val,f,c):
            if val < f: return f
            elif val > c: return c
            else: return val

        filled = []
        for wo in windows:
            w1off = self.tangent.copy().scale_u(wo[0])
            w1 = self.v1.copy().translate(w1off)
            w2off = self.tangent.copy().scale_u(wo[1])
            w2 = w1.copy().translate(w2off)

            wheight = mpu.clamp(int(0.5*self.wall_height),2.0,5.0)
            woff = wheight/2.0 + 1.0

            bheight = woff - wheight/2.0
            bottom = wa.wall(w1.copy(),w2.copy(),wall_height = bheight, 
                wall_width = self.wall_width,gaped = False,
                rid_top_bottom = False)

            hoff = woff + wheight/2.0
            hheight = self.wall_height - hoff
            w1.z += hoff 
            w2.z += hoff
            head = wa.wall(w1,w2,wall_height = hheight,
                wall_width = self.wall_width,
                gaped = False,rid_top_bottom = False)

            filled.append(head)
            filled.append(bottom)
        return filled

    def fill_doors(self, doors):

        def ______clamp(val,f,c):
            if val < f: return f
            elif val > c: return c
            else: return val

        filled = []
        for do in doors:
            d1off = self.tangent.copy().scale_u(do[0])
            d1 = self.v1.copy().translate(d1off)
            d2off = self.tangent.copy().scale_u(do[1])
            d2 = d1.copy().translate(d2off)

            dheight = mpu.clamp(int(0.75*self.wall_height),3.0,5.0)
            hheight = self.wall_height - dheight
            hoff = dheight
            d1.z += hoff
            d2.z += hoff
            head = wa.wall(d1,d2,wall_height = hheight,
                wall_width = self.wall_width, 
                rid_top_bottom = False,gaped = False)
            filled.append(head)
        return filled

    def build(self, solid = False, flh = 0.0, clh = 0.0):
        #print 'BUILD WALL!'

        wargs = {
            'rid_top_bottom':False,
            'wall_width':self.wall_width, 
            'wall_height':self.wall_height + flh + clh,
            'gaped':False, 
                }

        doorwidth = 3.0
        windowwidth = 3.0

        if solid:
            doors = []
            windows = []
        else:
            if self.sort == 'interior':
                if self.length > 2.0*doorwidth:
                    dpfa = rm.choice([0.25,0.5,0.75])
                    dpos = dpfa*self.length - doorwidth/2.0
                    doors = [[dpos,doorwidth]]
                else: doors = []
                windows = []
                doors.extend(windows)

            else:
                doors = []
                if self.length > 3.0*windowwidth:
                    w1pos = 0.25*self.length - windowwidth/2.0
                    w2pos = 0.75*self.length - windowwidth/2.0
                    windows = [
                        [w1pos,windowwidth], 
                        [w2pos,windowwidth]]
                elif self.length > 2.0*windowwidth:
                    w1pos = 0.5*self.length - windowwidth/2.0
                    windows = [[w1pos,windowwidth]]
                else: windows = []
                doors.extend(windows)

            if self.unswitchable:
                doorwidth = 3.0
                dpos = 0.5*self.length - doorwidth/2.0
                doors.insert(1,[dpos,doorwidth])

        wargs['gaps'] = doors

        #flh = 0.5
        #clh = 0.5
        v1 = self.v1.copy().translate_z(-flh)
        v2 = self.v2.copy().translate_z(-flh)

        pieces = [wa.wall(v1,v2,**wargs)]
        #pieces[0].primitives[0].rotate_z_face(
        #    self.rear_tip_rot,face = 'left')
        #pieces[0].primitives[-1].rotate_z_face(
        #    self.lead_tip_rot,face = 'right')
        pieces.extend(self.fill_doors(doors))
        pieces.extend(self.fill_windows(windows))
        return pieces

class floor_sector(blueprint):
    # a sector is a convex 2d projection of a space to be stitched to other
    # sectors to form a building floor plan
    # should be able to fill a space as necessary
    # a building is made of references to a list of floor_plans
    # each floor is pointed to a single plan
    # the plans are a chosen to stack appropriately geometrically

    def __init__(self, *args, **kwargs):
        self._default_('fgaps',[],**kwargs)
        self._default_('cgaps',[],**kwargs)
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
        blueprint.__init__(self, *args, **kwargs)

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
            c1,c2 = self.corners[cdx-1],self.corners[cdx]
            pairs.append((c1.copy(),c2.copy()))
        c1,c2 = self.corners[-1],self.corners[0]
        pairs.append((c1.copy(),c2.copy()))
        return pairs

    def build(self,floor = True,ceiling = True):
        #print 'BUILD FLOOR SECTOR!'

        pieces = []
        fargs = {
            'gaps':self.fgaps, 
            'position':self.position, 
            'length':self.length,
            'width':self.width, 
            'floor_height':self.floor_height, 
                }
        coff = self.ceiling_height + self.wall_height
        cargs = {
            'gaps':self.cgaps, 
            'position':self.position.copy().translate_z(coff), 
            'length':self.length,
            'width':self.width, 
            'floor_height':self.ceiling_height, 
                }

        if floor: pieces.append(fl.floor(**fargs))
        if ceiling: pieces.append(fl.floor(**cargs))
        return pieces

class floor_plan(blueprint):

    def __init__(self, *args, **kwargs):
        self._default_('length',50,**kwargs)
        self._default_('width',50,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('ceiling_height',0.5,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        self.interior_walls = []
        self.exterior_walls = []
        self.sectors = []
        self.set_story_height()
        self.divide_space()

    def set_story_height(self):
        self.story_height = self.floor_height +\
            self.wall_height + self.ceiling_height
        for ew in self.exterior_walls:
            ew.wall_height = self.wall_height
        for ew in self.interior_walls:
            ew.wall_height = self.wall_height
        for ew in self.sectors:
            ew.wall_height = self.wall_height
        return self.story_height

    def reduce_sectors(self, cuts = None):
        seccnt = len(self.sectors)
        if cuts is None: cuts = int(rm.choice([0.25,0.5,0.75])*seccnt) + 1
        extrawalls = []
        extrasects = []
        for cu in range(cuts):
            secw = rm.choice(self.exterior_walls).sector
            if secw in extrasects: continue
            extrasects.append(secw)
            swalls = []
            swalls.extend(secw.find_walls(self.exterior_walls))
            swalls.extend(secw.find_walls(self.interior_walls))
            for sw in swalls:
                if sw.sort == 'exterior':
                    if not sw in extrawalls:
                        extrawalls.append(sw)
                elif sw.sort == 'interior': self.switch_wall_sort(sw)
        for sc in extrasects: self.sectors.remove(sc)
        for ew in extrawalls: self.exterior_walls.remove(ew)
        # 
        print 'reduce should cut down the floor sectors'
    
    def resolve_walls(self,ewalls,iwalls,sect):
        # ewalls and iwalls are new but will be added soon
        eewalls = self.exterior_walls
        eiwalls = self.interior_walls
        
        def resolve_verts(shared,one,two):
            done = cv.distance(shared,one)
            dtwo = cv.distance(shared,two)
            if done < dtwo:
                ipair = [shared,one]
                epair = [one,two]
            elif done > dtwo:
                ipair = [shared,two]
                epair = [two,one]
            return ipair, epair

        newalls = []
        niwalls = []

        etoiwalls = []
        extrawalls = []

        for ew in ewalls: # for each new potential wall
            ewvs = [ew.v1,ew.v2] # positions of ew endpoints
            ewn = ew.normal.copy()
            ewt = ew.v1v2.copy().normalize()
            ewewnproj = mpbb.project(ewvs,ewn) # projection of ew onto ewn; always a dot

            for eew in eewalls: # for each existing exterior wall
                eewvs = [eew.v1,eew.v2] # positions of eew endpoints
                eewn = eew.normal.copy()
                eewt = eew.v1v2.copy().normalize()
                eeweewnproj = mpbb.project(eewvs,eewn) # projection of eew onto eewn; always a dot

                eewewnproj = mpbb.project(eewvs,ewn) # projection of eew onto ew
                eweewnproj = mpbb.project(ewvs,eewn) # projection of ew onto eew

                if mpbb.overlap(eewewnproj,ewewnproj) or\
                    mpbb.overlap(eweewnproj,eeweewnproj):
                    # if each wall is a dot in the other's normal projection, the overlap is parallel
                    if eewewnproj.x == eewewnproj.y and eweewnproj.x == eweewnproj.y:
                        # note that eewt and ewt are antiparallel typically
                        ewewtproj = mpbb.project(ewvs,ewt) # projection of ew onto ew tangent space
                        eewewtproj = mpbb.project(eewvs,ewt) # projection of eew onto ew tangent space
                        eweewtproj = mpbb.project(ewvs,eewt) # projection of ew onto eew tangent space
                        eeweewtproj = mpbb.project(eewvs,eewt) # projection of eew onto eew tangent space

                        # be sure they overlap in one another's tangent space
                        if mpbb.overlap(ewewtproj,eewewtproj) and\
                                mpbb.overlap(eweewtproj,eeweewtproj):

                            # make sure they are not just sharing an endpoint
                            if not ewewtproj.x == eewewtproj.y and\
                                    not ewewtproj.y == eewewtproj.x:

                                evals = ewvs + eewvs
            
                                # if theres a complete overlap
                                if ewewtproj.x == eewewtproj.x and\
                                        ewewtproj.y == eewewtproj.y:

                                    extrawalls.append(ew)
                                    etoiwalls.append(eew)

                                # if they share a single endpoint
                                elif ewewtproj.x == eewewtproj.x:
                                    if ewt == eewt:
                                        ipair,epair = resolve_verts(evals[0],evals[1],evals[3])
                                    elif ewt == cv.flip(eewt):
                                        ipair,epair = resolve_verts(evals[0],evals[1],evals[2])

                                    extrawalls.append(ew)
                                    extrawalls.append(eew)

                                    if ew.length > eew.length:
                                        epair.reverse()

                                    niw = wall_plan(*ipair, 
                                            sector = sect, 
                                            sort = 'interior', 
                                            wall_height = self.wall_height)
                                    new = wall_plan(*epair, 
                                            sector = sect, 
                                            sort = 'exterior', 
                                            wall_height = self.wall_height)
                                    niwalls.append(niw)
                                    newalls.append(new)

                                # or perhaps the other endpoint
                                elif ewewtproj.y == eewewtproj.y:

                                    if ewt == eewt:
                                        ipair,epair = resolve_verts(evals[1],evals[0],evals[2])
                                    elif ewt == cv.flip(eewt):
                                        ipair,epair = resolve_verts(evals[1],evals[0],evals[3])

                                    extrawalls.append(ew)
                                    extrawalls.append(eew)

                                    if ew.length > eew.length:
                                        epair.reverse()

                                    niw = wall_plan(*ipair, 
                                            sector = sect, 
                                            sort = 'interior', 
                                            wall_height = self.wall_height)
                                    new = wall_plan(*epair, 
                                            sector = sect, 
                                            sort = 'exterior', 
                                            wall_height = self.wall_height)
                                    niwalls.append(niw)
                                    newalls.append(new)

                                else:
                                    #print 'the complicated case'
                                    return False

                    # overlap is nonparallel
                    else:
                        ewewtproj = mpbb.project(ewvs,ewt) # projection of ew onto ew tangent space
                        eewewtproj = mpbb.project(eewvs,ewt) # projection of eew onto ew tangent space
                        eweewtproj = mpbb.project(ewvs,eewt) # projection of ew onto eew tangent space
                        eeweewtproj = mpbb.project(eewvs,eewt) # projection of eew onto eew tangent space

                        # be sure they overlap in one another's tangent space
                        if mpbb.overlap(ewewtproj,eewewtproj) and\
                                mpbb.overlap(eweewtproj,eeweewtproj):

                            if eweewtproj.x == eweewtproj.y and\
                                    (eweewtproj.x == eeweewtproj.x or\
                                        eweewtproj.x == eeweewtproj.y):
                                #print 'perp endpoint intersection...'
                                pass

                            elif eewewtproj.x == eewewtproj.y and\
                                    (eewewtproj.x == ewewtproj.x or\
                                        eewewtproj.x == ewewtproj.y):
                                #print 'perp endpoint intersection...'
                                pass

                            else:
                                #print 'perp overlap case'
                                return False

        for ew in extrawalls:
            if ew in ewalls: ewalls.remove(ew)
            if ew in iwalls: iwalls.remove(ew)
            if ew in eewalls: eewalls.remove(ew)
            if ew in eiwalls: eiwalls.remove(ew)
        [ewalls.append(new) for new in newalls]
        [iwalls.append(niw) for niw in niwalls]
        for ew in etoiwalls:self.switch_wall_sort(ew)
        return True

    def switch_wall_sort(self, wall):
        if wall.sort == 'interior':
            self.exterior_walls.append(wall)
            self.interior_walls.remove(wall)
            wall.sort = 'exterior'
            wall.face_away()
        elif wall.sort == 'exterior':
            self.exterior_walls.remove(wall)
            self.interior_walls.append(wall)
            wall.sort = 'interior'
            wall.face_away()

    def should_shaft(self,newpos,newl,neww):
            sdists = [cv.distance(newpos,sc.position) 
                            for sc in self.sectors]
            if not sdists: sdmin = 100
            else: sdmin = min(sdists)
            if sdmin > 20 and newl > 20 and neww > 20:
                shpos = newpos.copy()
                shl = 10
                shw = 12
                gaps = self.add_shaft(shpos,shl,shw)
                return gaps
            else: return []

    def add_shaft(self,pos,l,w):
            shargs = {
                'position':pos.copy(), 
                'length':l, 
                'width':w, 
                #'wall_heights':self.wall_heights, 
                #'floor_heights':self.floor_heights, 
                #'ceiling_heights':self.ceiling_heights, 
                    }
            gaps = [(cv.zero(),l,w)]
            self.shaft_kwargs.append(shargs)
            return gaps

    def grow(self,length = None,side = None):
        if side is None:
            side = rm.choice(self.exterior_walls)
            if side.unswitchable:
                print 'found the entrance while growing'
                return False

        if length is None:
            glengmax = 20 # this is decided by projecting each v1v2
            gleng = rm.choice([8,12,16,20,24,28,32])
        else: gleng = length

        side.face_away()
        c1 = side.v2.copy()
        c2 = side.v1.copy()
        cn = side.normal.copy()
        c3,c4 = extrude_edge(c1,c2,gleng,cn)
        newcorners = [c1,c2,c3,c4]
        sect = floor_sector(corners = newcorners, 
                floor_height = self.floor_height, 
                ceiling_height = self.ceiling_height, 
                wall_height = self.wall_height)
        scpos = sect.position
        scl = sect.length
        scw = sect.width
        gaps = self.should_shaft(scpos,scl,scw)
        sect.fgaps = gaps[:]
        sect.cgaps = gaps[:]
        for esect in self.sectors:
            ebb = esect.get_bboxes()
            nbb =  sect.get_bboxes()
            if mpbb.intersects(ebb,nbb):
                if gaps: self.shaft_kwargs.pop(-1)
                print 'new sect intersected!'
                return False

        cpairs = [(c2,c3),(c3,c4),(c4,c1)]
        extwalls = [wall_plan(*cp, 
            sector = sect, 
            sort = 'exterior', 
            wall_height = self.wall_height) 
                for cp in cpairs] 
        intwalls = []
        if self.resolve_walls(extwalls,intwalls,sect):
            self.switch_wall_sort(side)

            self.sectors.append(sect)
            self.exterior_walls.extend(extwalls)
            self.interior_walls.extend(intwalls)
            return True

        else: return False
    
    def build_basement(self,bottom = False):
        built = []
        porch = self.sectors.pop(1)
        for sector in self.sectors:
            if bottom:
                tgaps = sector.fgaps[:]
                sector.fgaps = []
            built.extend(sector.build())
            if bottom: sector.fgaps = tgaps
        for wall in self.exterior_walls:
            built.extend(wall.build(solid = True))
        #for wall in self.interior_walls: built.extend(wall.build())
        self.sectors.insert(1,porch)
        return built

    def build_lobby(self):
        built = []
        for sector in self.sectors:
            #sector.wall_height = self.wall_height
            built.extend(sector.build())
        for wall in self.exterior_walls: built.extend(wall.build())
        for wall in self.interior_walls: built.extend(wall.build())
        return built
    
    def build(self):
        built = []
        porch = self.sectors.pop(1)
        for sector in self.sectors:
            #sector.wall_height = self.wall_height
            built.extend(sector.build())
        for wall in self.exterior_walls:
            wswitch = wall.unswitchable
            wall.unswitchable = False
            built.extend(wall.build())
            wall.unswitchable = wswitch
        for wall in self.interior_walls: built.extend(wall.build())
        self.sectors.insert(1,porch)
        return built

    def build_rooftop(self):
        built = []
        porch = self.sectors.pop(1)
        for sector in self.sectors:
            built.extend(sector.build(ceiling = False))
        for wall in self.exterior_walls:
            wall.wall_height = 1.0
            built.extend(wall.build(solid = True))
        #for wall in self.interior_walls: built.extend(wall.build())
        self.sectors.insert(1,porch)
        return built

    def get_shaft_plans(self):
        return self.shaft_kwargs

    def main_space(self):
        l,w = self.length,self.width
        subl = rm.choice([0.5*l,0.75*l,l])
        subw = rm.choice([0.5*w,0.75*w,w])
        mx = -l + subl
        my = -w + subw
        pos = cv.vector(mx,my,0)

        self.shaft_kwargs = []
        sect = floor_sector(
            floor_height = self.floor_height, 
            ceiling_height = self.ceiling_height, 
            wall_height = self.wall_height, 
            length = subl, 
            width = subw, 
            position = pos)
        gaps = self.should_shaft(sect.position,subl,subw)
        sect.fgaps = gaps[:]
        sect.cgaps = gaps[:]
        cpairs = sect.wall_verts()
        extwalls = [wall_plan(*cp, 
            sector = sect, 
            sort = 'exterior', 
            wall_height = self.wall_height) 
                for cp in cpairs]
        intwalls = []

        self.interior_walls = intwalls
        self.exterior_walls = extwalls
        self.sectors = [sect]
        
        self.entrance = extwalls[0]
        porch_length = 8
        self.grow(porch_length,self.entrance)
        self.porch = self.sectors[-1]
        self.exterior_walls.pop(-1)
        self.exterior_walls.pop(-1)
        self.exterior_walls.pop(-1)
        self.switch_wall_sort(self.entrance)
        self.entrance.unswitchable = True

    def order_exterior_walls(self):
        def find_next(av2):
            for edx in range(len(ewalls)):
                ew = ewalls[edx]
                if cv.near(ew.v1,av2):
                    return edx
        ewalls = self.exterior_walls
        ordered = []
        ordered.append(ewalls.pop(0))
        while ewalls:
            lastv2 = ordered[-1].v2
            ndx = find_next(lastv2)
            if ndx is None:ordered.append(ewalls.pop(0))
            else:ordered.append(ewalls.pop(ndx))
        self.exterior_walls = ordered

    def join_walls(self):
        self.order_exterior_walls()
        ewalls = self.exterior_walls
        for ew in ewalls:ew.face_away()

        n1 = ewalls[-1].normal.copy().xy()
        n2 = ewalls[0].normal.copy().xy()
        n3 = ewalls[1].normal.copy().xy()

        ewcnt = len(ewalls)
        for wdx in range(ewcnt):
            pdx = wdx - 1
            ndx = wdx + 1 if wdx < ewcnt - 1 else 0
            ew = ewalls[wdx]
            pw = ewalls[pdx]
            nw = ewalls[ndx]

            n1 = pw.normal.copy().xy()
            n2 = ew.normal.copy().xy()
            n3 = nw.normal.copy().xy()

            angle1 = -1.0*cv.angle_between(n1,n2)/2.0
            angle2 =      cv.angle_between(n2,n3)/2.0
        
            ew.rear_tip_rot = angle1
            ew.lead_tip_rot = angle2
        
        print 'finish join walls function!'

    def divide_space(self):
        #sections = rm.choice([5,6,7,8,9,10])
        sections = 25
        self.main_space()
        for sect in range(sections):
            if not self.grow(): print 'growth rejected'
            #if not self.grow(): break
        print '\n\tgrew', sect, 'of', sections
        #self.join_walls()

class building_plan(blueprint):

    def __init__(self, *args, **kwargs):
        self._default_('floors',10,**kwargs)
        self._default_('basements',2,**kwargs)

        self.st0plan = floor_plan()

        self.wall_heights = [10]*self.basements
        self.wall_heights.extend([8,6,6])
        self.wall_heights.extend([4]*(self.floors - 3))

        shargs = self.st0plan.get_shaft_plans()
        for sh in shargs:
            # this will break when the floor_height or ceiling_height change
            sh['position'].translate_z(-11.0*self.basements)
            sh['floors'] = self.floors + self.basements
            sh['wall_heights'] = self.wall_heights[:]

            #'wall_heights':self.wall_heights, 
            #'floor_heights':self.floor_heights, 
            #'ceiling_heights':self.ceiling_heights, 

        self.shaft_plans = [shaft_plan(**sh) for sh in shargs]

    def build_shafts(self):
        shplans = self.shaft_plans
        shafts = []
        for shplan in shplans:
            shafts.extend(shplan.build())
        return shafts

    def build_foundation(self):
        bacount = self.basements
        whopts = self.wall_heights
        basements = []
        newstpos = cv.vector(0,0,0)
        for stdx in range(bacount):
            this_st_plan = self.st0plan
            this_st_plan.wall_height = whopts.pop(0)
            this_st_plan.set_story_height()
            newstpos = newstpos.copy()
            newstpos.z -= this_st_plan.story_height
            newpieces = this_st_plan.build_basement(
                        bottom = stdx == bacount - 1)
            newstory = sg.node(
                children = newpieces, 
                consumes_children = True, 
                position = newstpos)
            basements.append(newstory)
        return basements

    def build_stories(self):

        def roll_for_reduction(sdx):
            return rm.random()*(float(sdx)/flcount) > 0.2

        flcount = self.floors
        stories = []
        newstpos = cv.vector(0,0,0)
        whopts = self.wall_heights

        reduces = 1

        for stdx in range(flcount):
            this_st_plan = self.st0plan
            this_st_plan.wall_height = whopts.pop(0)
            this_st_plan.set_story_height()

            if roll_for_reduction(stdx) and reduces > 0:
                reduces -= 1
                this_st_plan.reduce_sectors()

            if stdx == 0: newpieces = this_st_plan.build_lobby()
            else: newpieces = this_st_plan.build()
            newstory = sg.node(
                children = newpieces, 
                consumes_children = True, 
                position = newstpos)
            stories.append(newstory)
            newstpos = newstpos.copy()
            newstpos.z += this_st_plan.story_height
        self.roof_position = newstpos
        return stories

    def build_rooftop(self):
        rooftop = []
        newstpos = self.roof_position
        this_st_plan = self.st0plan
        newpieces = this_st_plan.build_rooftop()
        newstory = sg.node(
            children = newpieces, 
            consumes_children = True,
            position = newstpos)
        rooftop.append(newstory)
        return rooftop

    def build(self):
        built = self.build_foundation()
        built.extend(self.build_stories())
        built.extend(self.build_rooftop())
        built.extend(self.build_shafts())
        return built









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
    return outline
    #return circumscribe_box(corners,outline)

def outline_test(center):
    c1 = cv.vector(-10,-10,0)
    c2 = cv.vector( 10,-10,0)
    c3 = cv.vector( 10, 10,0)
    c4 = cv.vector(-10, 10,0)
    corners = [c1,c2,c3,c4]
    cv.translate_coords(corners,center)
    outy = walk_line(corners)
    return outy








