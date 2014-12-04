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
        self._default_('floor_height',0.5,**kwargs)
        self._default_('ceiling_height',0.5,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        self._default_('length',8,**kwargs)
        self._default_('width',8,**kwargs)
        self._default_('floor_count',3,**kwargs)

    def build(self):
        pieces = []
        shargs = {
            'position':self.position, 
            'floor_height':self.floor_height, 
            'ceiling_height':self.ceiling_height, 
            'wall_height':self.wall_height, 
            'length':self.length, 
            'width':self.width, 
            'floors':self.floor_count, 
                }
        pieces.append(st.shaft(**shargs))
        return pieces

class wall_plan(blueprint):
    def __init__(self,v1,v2,sector = None,sort = 'exterior',**kwargs):
        self.sort = sort
        self.sector = sector
        self._default_('wall_width',0.5,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        self.v1 = v1
        self.v2 = v2
        self.v1v2 = cv.v1_v2(v1,v2)
        self.lead_tip_rot = 0.0
        self.rear_tip_rot = 45.0
        self.length = self.v1v2.magnitude()
        self.normal = cv.cross(self.v1v2,cv.zhat).normalize()
        self.tangent = self.v1v2.copy().normalize()

    def face_away(self):
        intpt = self.sector.position
        midpt = cv.midpoint(self.v1,self.v2)
        tstpt = midpt.copy().translate(self.normal)
        if cv.distance(intpt,midpt) > cv.distance(intpt,tstpt):
            self.normal.flip()

    def fill_windows(self, windows):
        filled = []
        for wo in windows:
            w1off = self.tangent.copy().scale_u(wo[0])
            w1 = self.v1.copy().translate(w1off)
            w2off = self.tangent.copy().scale_u(wo[1])
            w2 = w1.copy().translate(w2off)
            bottom = wa.wall(w1.copy(),w2.copy(),
                wall_height = 1.0, wall_width = self.wall_width, 
                gaped = False,rid_top_bottom = False)
            hoff = self.wall_height - 1.0
            w1.z += hoff 
            w2.z += hoff
            head = wa.wall(w1,w2,wall_height = 1.0,
                wall_width = self.wall_width,
                gaped = False,rid_top_bottom = False)
            filled.append(head)
            filled.append(bottom)
        return filled

    def fill_doors(self, doors):
        filled = []
        for do in doors:
            d1off = self.tangent.copy().scale_u(do[0])
            d1 = self.v1.copy().translate(d1off)
            d2off = self.tangent.copy().scale_u(do[1])
            d2 = d1.copy().translate(d2off)
            hoff = self.wall_height - 1.0
            d1.z += hoff
            d2.z += hoff
            head = wa.wall(d1,d2,wall_height = 1.0,
                wall_width = self.wall_width, 
                rid_top_bottom = False,gaped = False)
            filled.append(head)
        return filled

    def build(self):
        #print 'BUILD WALL!'

        wargs = {
            'rid_top_bottom':False,
            'wall_width':self.wall_width, 
            'wall_height':self.wall_height,
            'gaped':False, 
                }

        if self.sort == 'interior':
            dpos = rm.choice([0.25,0.5,0.75])
            if self.length > 3.0:
                doors = [[dpos*self.length-1.0,2.0]]
            else: doors = []
            windows = []
            doors.extend(windows)
            wargs['gaps'] = doors

        else:
            doors = []
            if self.length > 8.0:
                windows = [
                    [0.25*self.length-1.5,3.0], 
                    [0.75*self.length-1.5,3.0]]
            else: windows = []
            doors.extend(windows)
            wargs['gaps'] = doors
            #wargs['gaped'] = True

        pieces = [wa.wall(self.v1,self.v2,**wargs)]
        pieces[0].primitives[0].rotate_z_face(fu.to_rad(
            self.rear_tip_rot),face = 'left')
        pieces[0].primitives[-1].rotate_z_face(fu.to_rad(
            self.lead_tip_rot),face = 'right')
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
        self._default_('gaps',[],**kwargs)
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
        small_corners = [
            c.copy().translate(tv) for c,tv in 
                zip(self.corners,com_vects)]
        self.bboxes = [mpbb.bbox(corners = small_corners)]

    def get_bboxes(self):
        return self.bboxes

    def wall_verts(self):
        pairs = []
        ccnt = len(self.corners)
        for cdx in range(1,ccnt):
            c1,c2 = self.corners[cdx-1],self.corners[cdx]
            pairs.append((c1.copy(),c2.copy()))
        c1,c2 = self.corners[-1],self.corners[0]
        pairs.append((c1.copy(),c2.copy()))
        return pairs

    def build(self):
        #print 'BUILD FLOOR SECTOR!'

        pieces = []
        fargs = {
            'gaps':self.gaps, 
            'position':self.position, 
            'length':self.length,
            'width':self.width, 
            'floor_height':self.floor_height, 
                }
        coff = self.ceiling_height + self.wall_height
        cargs = {
            'gaps':self.gaps, 
            'position':self.position.copy().translate_z(coff), 
            'length':self.length,
            'width':self.width, 
            'floor_height':self.ceiling_height, 
                }

        pieces.append(fl.floor(**fargs))
        pieces.append(fl.floor(**cargs))
        return pieces

class floor_plan(blueprint):

    def __init__(self, *args, **kwargs):
        self._default_('length',50,**kwargs)
        self._default_('width',50,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('ceiling_height',0.5,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        self.story_height = self.floor_height +\
            self.wall_height + self.ceiling_height

        #self.story_height *= 2.0

        self.interior_walls = []
        self.exterior_walls = []
        self.sectors = []
        self.shafts = []
        self.divide_space()
    
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
            else:
                print 'this happens?!'
                pdb.set_trace()
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

                                    #if not ew in extrawalls:extrawalls.append(ew)
                                    extrawalls.append(ew)
                                    #eew.sort = 'interior'
                                    etoiwalls.append(eew)

                                # if they share a single endpoint
                                elif ewewtproj.x == eewewtproj.x:
                                    if ewt == eewt:
                                        #print 'yea?', evals[0] == evals[2]
                                        ipair,epair = resolve_verts(evals[0],evals[1],evals[3])
                                    elif ewt == cv.flip(eewt):
                                        #print 'or?', evals[0] == evals[3]
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
            
                                    #for ev in evals: print ev
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
                                print 'perp overlap case'
                                #pdb.set_trace()
                                return False

        for ew in extrawalls:
            if ew in ewalls: ewalls.remove(ew)
            if ew in iwalls: iwalls.remove(ew)
            if ew in eewalls: eewalls.remove(ew)
            if ew in eiwalls: eiwalls.remove(ew)
        [ewalls.append(new) for new in newalls]
        [iwalls.append(niw) for niw in niwalls]

        for ew in etoiwalls:
            self.exterior_walls.remove(ew)
            self.interior_walls.append(ew)
            ew.sort = 'interior'
            ew.face_away()

        return True

    def should_shaft(self,newpos,newl,neww):
            sdists = [cv.distance(newpos,sc.position) 
                            for sc in self.sectors]
            if not sdists: sdmin = 0
            else: sdmin = min(sdists)
            if sdmin > 20 and newl > 16 and neww > 16:
                #shpos = cv.zero()
                shpos = newpos.copy()
                shl = 8
                shw = 8
                gaps = self.add_shaft(shpos,shl,shw)
                return gaps
            else: return []

    def add_shaft(self,pos,l,w):
            shargs = {
                'position':pos.copy(), 
                'length':l, 
                'width':w, 
                'wall_height':self.wall_height, 
                'floor_height':self.floor_height, 
                'ceiling_height':self.ceiling_height, 
                    }
            gaps = [(cv.zero(),l,w)]
            self.shaft_kwargs.append(shargs)
            return gaps

    def grow(self):
        side = rm.choice(self.exterior_walls)
        glengmax = 20 # this is decided by projecting each v1v2
        gleng = rm.choice([8,12,16,20])

        side.face_away()
        c1 = side.v2.copy()
        c2 = side.v1.copy()
        cn = side.normal
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
        sect.gaps = gaps
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
        intwalls = [side]
        if self.resolve_walls(extwalls,intwalls,sect):
            side.sort = 'interior'
            self.exterior_walls.remove(side)

            self.sectors.append(sect)
            self.exterior_walls.extend(extwalls)
            self.interior_walls.extend(intwalls)
            return True

        else: return False

    def build(self):
        built = []
        for sector in self.sectors: built.extend(sector.build())
        for wall in self.exterior_walls: built.extend(wall.build())
        for wall in self.interior_walls: built.extend(wall.build())
        for shft in self.shafts: built.extend(shft.build())
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
        sect.gaps = self.should_shaft(sect.position,subl,subw)
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

    def join_walls(self):
        # order them tip to tail
        # for each consider the previous and next tangents
        # set the rear_tip_rot to the inverse of previous lead_tip_rot

        rt = self.exterior_walls[-1].v1v2
        ewcnt = len(self.exterior_walls)
        for wdx in range(ewcnt):
            pdx = wdx - 1
            ndx = wdx + 1 if wdx < ewcnt - 1 else 0
            ew = self.exterior_walls[wdx]
            pw = self.exterior_walls[pdx]
            nw = self.exterior_walls[ndx]
            ew.rear_tip_rot = -1.0*pw.lead_tip_rot
        print 'finish join walls function!'

    def divide_space(self):
        #sections = rm.choice([5,6,7,8,9,10])
        sections = 40
        self.main_space()
        for sect in range(sections):
            if not self.grow(): print 'growth rejected'
            #if not self.grow(): break
        print '\n\tgrew', sect, 'of', sections
        self.join_walls()

class building_plan(blueprint):

    def __init__(self, *args, **kwargs):
        self._default_('floor_count',4,**kwargs)

        self.st0plan = floor_plan()

        shargs = self.st0plan.get_shaft_plans()
        for sh in shargs:
            sh['floor_count'] = self.floor_count

        self.shaft_plans = [shaft_plan(**sh) for sh in shargs]

    def build_shafts(self):
        shplans = self.shaft_plans
        shafts = []
        for shplan in shplans:
            shafts.extend(shplan.build())
        return shafts

    def build_stories(self):
        flcount = self.floor_count
        stories = []
        newstpos = cv.vector(0,0,0)
        for stdx in range(flcount):
            this_st_plan = self.st0plan
            newpieces = this_st_plan.build()
            newstory = sg.node(
                children = newpieces, 
                consumes_children = True, 
                position = newstpos)
            stories.append(newstory)
            newstpos = newstpos.copy()
            newstpos.z += this_st_plan.story_height
        return stories

    def build(self):
        built = self.build_stories()
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









