import make_places.scenegraph as sg
import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.blueprints as mbp
import make_places.floors as fl
import make_places.walls as wa
import make_places.stairs as st

import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

import random as rm
import os

import pdb

class floor_plan(mbp.blueprint):

    def __init__(self, *args, **kwargs):
        self._default_('length',100,**kwargs)
        self._default_('width',50,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('max_sections',25,**kwargs)
        self._default_('ceiling_height',0.5,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        self.corners = mpu.make_corners(cv.zero(),self.length,self.width,0)
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
            ew.floor_height = self.floor_height
            ew.ceiling_height = self.ceiling_height
        for ew in self.interior_walls:
            ew.wall_height = self.wall_height
            ew.floor_height = self.floor_height
            ew.ceiling_height = self.ceiling_height
        for ew in self.sectors:
            ew.wall_height = self.wall_height
            ew.floor_height = self.floor_height
            ew.ceiling_height = self.ceiling_height
        return self.story_height

    def reduce_sectors(self, cuts = None):
        seccnt = len(self.sectors)
        if cuts is None: cuts = int(rm.choice([0.25,0.5,0.75])*seccnt) + 1
        extrawalls = []
        extrasects = []
        for cu in range(cuts):
            secw = rm.choice(self.exterior_walls).sector
            if not secw.reducible(self.exterior_walls): continue
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
        #print 'reduce should cut down the floor sectors'
    
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

                                    niw = wa.wall_plan(*ipair, 
                                            sector = sect,sort = 'interior', 
                                            wall_height = self.wall_height)
                                    new = wa.wall_plan(*epair, 
                                            sector = sect,sort = 'exterior', 
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

                                    niw = wa.wall_plan(*ipair,sector = sect,sort = 'interior', 
                                            wall_height = self.wall_height)
                                    new = wa.wall_plan(*epair,sector = sect,sort = 'exterior',
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
            if sdmin > 20 and newl >= 20 and neww >= 20:
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

    def grow(self,length = None,side = None,force = False):
        if side is None:
            side = rm.choice(self.exterior_walls)
            if side.unswitchable:
                #print 'found the entrance while growing'
                return False

        if length is None:
            glengmax = 20 # this is decided by projecting each v1v2
            gleng = rm.choice([8,12,16,20,24,28,32])
        else: gleng = length

        bdist = side.distance_to_border(self.corners)
        if bdist < 8 and not force:
            #print 'too close to a border to grow'
            return False
        elif gleng > bdist: gleng = bdist

        side.face_away()
        c1 = side.v2.copy()
        c2 = side.v1.copy()
        cn = side.normal.copy()
        c3,c4 = mbp.extrude_edge(c1,c2,gleng,cn)
        newcorners = [c1,c2,c3,c4]
        sect = fl.floor_sector(corners = newcorners, 
                floor_height = self.floor_height, 
                ceiling_height = self.ceiling_height, 
                wall_height = self.wall_height)
        gaps = self.should_shaft(sect.position,sect.length,sect.width)
        sect.fgaps = gaps[:]
        sect.cgaps = gaps[:]
        if gaps: sect.shafted = True
        for esect in self.sectors:
            ebb = esect.get_bboxes()
            nbb =  sect.get_bboxes()
            if mpbb.intersects(ebb,nbb):
                if gaps: self.shaft_kwargs.pop(-1)
                #print 'new sect intersected!'
                return False

        cpairs = [(c2,c3),(c3,c4),(c4,c1)]
        extwalls = [wa.wall_plan(*cp, 
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
    
    def build_basement_lod(self,bottom = False):
        built = []
        porch = self.sectors.pop(1)
        for sector in self.sectors:
            built.extend(sector.build_lod())

        #for b in built: b.converts_to_lod = True
        self.sectors.insert(1,porch)
        return built

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

    def build_lobby_lod(self):
        built = []
        for sector in self.sectors:
            built.extend(sector.build_lod())
        return built

    def build_lobby(self):
        built = []
        for sector in self.sectors: built.extend(sector.build())
        for wall in self.exterior_walls: built.extend(wall.build())
        for wall in self.interior_walls: built.extend(wall.build())
        return built
    
    def build_lod(self):
        built = []
        porch = self.sectors.pop(1)
        for sector in self.sectors:
            built.extend(sector.build_lod())
        self.sectors.insert(1,porch)
        return built

    def build(self):
        built = []
        porch = self.sectors.pop(1)
        for sector in self.sectors:
            built.extend(sector.build())
        for wall in self.exterior_walls:
            wswitch = wall.unswitchable
            wall.unswitchable = False
            built.extend(wall.build(skirt = True))
            wall.unswitchable = wswitch
        for wall in self.interior_walls: built.extend(wall.build())
        self.sectors.insert(1,porch)
        return built

    def build_rooftop_lod(self):
        built = []
        porch = self.sectors.pop(1)
        for sector in self.sectors:
            if sector.shafted:
                tgaps = sector.cgaps[:]
                sector.cgaps = []
                built.extend(sector.build_lod())
                sector.cgaps = tgaps
            else:
                built.extend(sector.build(hasceiling = False))
        for wall in self.exterior_walls:
            if wall.sector.shafted:
                built.extend(wall.build())
            else:
                wh = wall.wall_height
                wall.wall_height = 1.0
                built.extend(wall.build(solid = True))
                wall.wall_height = wh
        for wall in self.interior_walls:
            if wall.sector.shafted:
                built.extend(wall.build())
        self.sectors.insert(1,porch)
        return built

    def build_rooftop(self):
        built = []
        porch = self.sectors.pop(1)
        for sector in self.sectors:
            if sector.shafted:
                tgaps = sector.cgaps[:]
                sector.cgaps = []
                built.extend(sector.build())
                sector.cgaps = tgaps
            else:
                built.extend(sector.build(hasceiling = False))
        for wall in self.exterior_walls:
            wswitch = wall.unswitchable
            wall.unswitchable = False
            if wall.sector.shafted:
                built.extend(wall.build())
            else:
                wh = wall.wall_height
                wall.wall_height = 1.0
                built.extend(wall.build(solid = True))
                wall.wall_height = wh
            wall.unswitchable = wswitch
        for wall in self.interior_walls:
            if wall.sector.shafted:
                built.extend(wall.build())
        self.sectors.insert(1,porch)
        return built

    def get_shaft_plans(self):
        return self.shaft_kwargs

    def main_space(self):
        l,w = self.length,self.width
        subl = rm.choice([0.25*l,0.5*l,0.75*l])
        subw = rm.choice([0.25*w,0.5*w,0.75*w])
        subl = mpu.clamp(subl,20,l)
        subw = mpu.clamp(subw,20,l)
        mx = -l/2.0 + subl/2.0
        my = -w/2.0 + 8 + subw/2.0
        mx = 0.0
        my = - w/2.0 + subw/2.0 + 10.0

        # could mx,my be correlated with the lod offset problem?
        #print 'lwslsw',l,w,subl,subw,mx,my

        pos = cv.vector(mx,my,0)
        #pos = cv.zero() # this investigates the above question

        self.shaft_kwargs = []
        sect = fl.floor_sector(
            floor_height = self.floor_height, 
            ceiling_height = self.ceiling_height, 
            wall_height = self.wall_height, 
            length = subl, 
            width = subw, 
            position = pos)
        gaps = self.should_shaft(sect.position,subl,subw)
        sect.fgaps = gaps[:]
        sect.cgaps = gaps[:]
        if gaps: sect.shafted = True
        cpairs = sect.wall_verts()
        extwalls = [wa.wall_plan(*cp, 
            sector = sect, 
            sort = 'exterior', 
            wall_height = self.wall_height) 
                for cp in cpairs]
        intwalls = []

        self.interior_walls = intwalls
        self.exterior_walls = extwalls
        self.sectors = [sect]
        
        self.entrance = extwalls[0]
        porch_length = 6
        self.grow(porch_length,self.entrance,True)
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
        
        #print 'finish join walls function!'

    def divide_space(self):
        sections = self.max_sections
        self.main_space()
        for sect in range(sections):
            grew = self.grow()
            if grew is False:
                #print 'growth rejected'
                pass
            elif grew is None:
                #print 'division aborted'
                break
        #print '\n\tgrew', sect, 'of', sections
        #self.join_walls()

batch_count = 0
class building_plan(mbp.blueprint):

    def __init__(self, *args, **kwargs):
        self._default_('length',200,**kwargs)
        self._default_('width',200,**kwargs)
        self._default_('floors',10,**kwargs)
        self._default_('basements',2,**kwargs)
        self.corners = mpu.make_corners(cv.zero(), 
                        self.length,self.width,0)

        self.st0plan = floor_plan(
            length = self.length, width = self.width)

        self.floor_heights = [1]*self.basements
        self.floor_heights.extend([0.8,0.8,0.8])
        self.floor_heights.extend([0.5]*(self.floors - 3))

        self.floor_heights = [0.5]*(self.floors + self.basements)

        self.ceiling_heights = [1]*self.basements
        self.ceiling_heights.extend([0.8,0.8,0.8])
        self.ceiling_heights.extend([0.5]*(self.floors - 3))

        self.ceiling_heights = [0.5]*(self.floors + self.basements)

        self.wall_heights = [10]*self.basements
        self.wall_heights.extend([8,6,6])
        self.wall_heights.extend([4]*(self.floors - 3))

        shargs = self.st0plan.get_shaft_plans()
        for sh in shargs:
            # this will break when the floor_height or ceiling_height change
            sh['position'].translate_z(-11.0*self.basements)
            sh['floors'] = self.floors + self.basements
            sh['wall_heights'] = self.wall_heights[:]
            sh['floor_heights'] = self.floor_heights[:]
            sh['ceiling_heights'] = self.ceiling_heights[:]

        self.shaft_plans = [st.shaft_plan(**sh) for sh in shargs]

    def build_fence(self):
        fence = []
        pwarg = {
            'corners':self.corners, 
            'gaped':False, 
            'rid_top_bottom_walls':False, 
            'consumes_children':True, 
                }
        pfwarg = {
            'position':cv.zero(), 
            'length':self.length, 
            'width':self.width, 
                }
        fence.append(wa.perimeter(**pwarg))
        #fence.append(fl.floor(**pfwarg))
        return fence

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
        
        newstpos = cv.zero()
        for stdx in range(bacount):
            this_st_plan = self.st0plan
            this_st_plan.wall_height = whopts.pop(0)
            this_st_plan.set_story_height()
            newstpos = newstpos.copy()
            newstpos.z -= this_st_plan.story_height

            newpieces = this_st_plan.build_basement(
                        bottom = stdx == bacount - 1)

            lodpieces = this_st_plan.build_basement_lod(
                        bottom = stdx == bacount - 1)
            newpieces.extend(lodpieces)

            newstory = sg.node(
                name = 'abasement' + str(stdx), 
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
        fhopts = self.floor_heights
        chopts = self.ceiling_heights

        reduces = 3

        for stdx in range(flcount):
            this_st_plan = self.st0plan
            this_st_plan.wall_height = whopts.pop(0)
            this_st_plan.floor_height = fhopts.pop(0)
            this_st_plan.ceiling_height = chopts.pop(0)
            this_st_plan.set_story_height()

            if roll_for_reduction(stdx) and reduces > 0:
                reduces -= 1
                this_st_plan.reduce_sectors()

            if stdx == 0:
                newpieces = this_st_plan.build_lobby()
                lodpieces = this_st_plan.build_lobby_lod()
            
            else:
                newpieces = this_st_plan.build()
                lodpieces = this_st_plan.build_lod()
            newpieces.extend(lodpieces)

            newstory = sg.node(
                name = 'astory' + str(stdx), 
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

        lodpieces = this_st_plan.build_rooftop_lod()
        newpieces.extend(lodpieces)

        newstory = sg.node(
            name = 'aroof', 
            children = newpieces, 
            consumes_children = True,
            position = newstpos)
        rooftop.append(newstory)
        return rooftop
    
    def batch_name(self):
        global batch_count
        name = '_story_batch_' + str(batch_count)
        batch_count += 1
        return name

    def batch_stories(self, stories):
        stcnt = len(stories)

        max_batch_number = 10
        stheight = self.st0plan.story_height
        batch_number = int(((self.length+self.width)/2.0)/stheight)
        batch_number = int(mpu.clamp(batch_number,1,max_batch_number))
        if batch_number == 1: return stories

        batches = []
        dex0 = 0
        while dex0 < stcnt:
            sts_left = stcnt - dex0
            if sts_left >= batch_number: 
                sts_this_round = batch_number
            else: sts_this_round = sts_left % batch_number
            this_batchs = stories[dex0:dex0+sts_this_round]
            dex0 += sts_this_round

            batch = sg.node(name = self.batch_name(), 
                children = this_batchs,consumes_children = True)
            batches.append(batch)

        return batches

    def build(self):
        found = self.build_foundation()
        stories = self.build_stories()
        rooftop = self.build_rooftop()
        shafts = self.build_shafts()
        #fence = self.build_fence()
        built = []
        built.extend(found)
        built.extend(stories)
        built.extend(rooftop)
        built = self.batch_stories(built)
        built.extend(shafts)
        #built.extend(fence)
        return built

_building_count_ = 0
class building(sg.node):

    def get_name(self):
        global _building_count_
        nam = 'building ' + str(_building_count_)
        _building_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        if kwargs.has_key('length') and kwargs['length'] < 40:
            kwargs['length'] = 40
        if kwargs.has_key('width') and kwargs['width'] < 40:
            kwargs['width'] = 40
        self._default_('name',self.get_name(),**kwargs)
        self._default_('length',40,**kwargs)
        self._default_('width',40,**kwargs)
        self._default_('tform',
            self.def_tform(*args,**kwargs),**kwargs)
        kwargs['uv_scales'] = cv.vector(10,10,10)
        self._default_('uv_tform',
            self.def_uv_tform(*args,**kwargs),**kwargs)
        self.building_plan = building_plan(**kwargs)
        children = self.building_plan.build()

        for ch in children:
            ch.uv_tform.parent = self.uv_tform

        self.add_child(*children)
        sg.node.__init__(self, *args, **kwargs)
        self.assign_material('concrete')

        print 'built building', _building_count_

    def get_bbox(self, *args, **kwargs):
        cornas = self.find_corners()
        #bb = mpbb.bbox(corners = cornas)
        #bb = mpbb.xy_bbox(corners = cornas,owner = self)
        bb = mpbb.xy_bbox(corners = cornas)
        return bb

    def terrain_points(self):
        tpts = self.find_corners()
        cv.translate_coords(tpts,cv.vector(0,0,-0.5))
        center = cv.center_of_mass(tpts)
        center.translate(cv.zero().translate_z(-0.5))
        tpts = mpu.dice_edges(tpts, dices = 1)
        tpts.append(center)
        return tpts

    def terrain_holes(self):
        tpts = [self.find_corners()]
        return tpts

    def find_corners(self):
        length = self.length + 2.0
        width = self.width + 2.0
        ttf = self.tform
        #ttf = self.tform.true()
        pos = ttf.position
        zang = ttf.rotation.z
        corners = mpu.make_corners(pos,length,width,zang)
        return corners






