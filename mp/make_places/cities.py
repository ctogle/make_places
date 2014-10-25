import make_places.fundamental as fu
#from make_places.fundamental import element
from make_places.scenegraph import node
from make_places.fundamental import bbox
from make_places.roads import road_system
from make_places.buildings import building

from math import sqrt
import numpy as np
import random as rm

class block(node):

    bl_themes = {
        #'suburbs' : (20,3,30,20), 
        #'residential' : (10,10,60,60), 
        #'park' : (3,1,10,10), 
        #'commercial' : (20,20,100,100), 
        'industrial' : (20,6,80,80), 
            }
    themes = [ke for ke in bl_themes.keys()]

    def __init__(self, *args, **kwargs):
        bth = rm.choice(self.themes)
        self._default_('theme',bth,**kwargs)
        blbc,blfc,blbl,blbw = self.bl_themes[self.theme]
        self._default_('max_floor_count',blfc,**kwargs)
        self._default_('max_building_length',blbl,**kwargs)
        self._default_('max_building_width',blbw,**kwargs)
        self._default_('building_count',blbc,**kwargs)
        if 'road' in kwargs.keys():
            rd = kwargs['road']
            children = self.make_buildings_from_road(*args, **kwargs)
        else:
            pos = kwargs['position']
            length = kwargs['length']
            width = kwargs['width']
            self.corners = self.find_corners(pos, length, width)
            children = self.make_buildings(*args, **kwargs)
        self._default_('children', children, **kwargs)
        node.__init__(self, *args, **kwargs)

    def find_corners(self, pos, length, width):
        c1, c2, c3, c4 = pos[:], pos[:], pos[:], pos[:]
        c2[0] += length
        c3[0] += length
        c3[1] += width
        c4[1] += width
        return [c1, c2, c3, c4]

    def make_buildings_from_road(self, *args, **kwargs):
        bboxes = kwargs['bboxes']
        rd = kwargs['road']
        rdside = kwargs['side']
        corns = rd.segmented_vertices
        #print('segverts',corns)
        corncnt = len(corns)
        zhat = [0,0,1]
        thats = [fu.normalize(fu.v1_v2(corns[dx],corns[dx-1])) 
                for dx in range(1,corncnt)]
        rdnorms = [fu.cross(that,zhat) for that in thats]
        bcnt = self.building_count
        #bcnt = 10
        buildings = []
        for bdx in range(bcnt):
            bname = 'building_' + str(bdx)
            flcnt = self.get_building_floor_count()
            bpos,blen,bwid,bhei,ang =\
                self.get_building_position_from_road(
                    corns,rdnorms,flcnt,side = rdside, 
                    road = rd,bboxes = bboxes)
            if not bpos is False:
                blarg = {
                    'name':bname, 
                    'position':bpos, 
                    'length':blen, 
                    'width':bwid, 
                    'floor_height':0.5, 
                    'wall_width':0.4, 
                    'wall_height':4.0, 
                    'floors':flcnt, 
                    'rotation':[0,0,ang], 
                        }
                buildings.append(building(**blarg))
                bboxes.extend(buildings[-1].get_bbox())
        self.buildings = buildings
        return buildings

    def get_building_position_from_road(self, 
            corners, rdnorms, flcnt, **kwargs):
        bboxes = kwargs['bboxes']
        road = kwargs['road']
        rdwidth = road.road_width
        rdrtside = kwargs['side'] == 'right'

        segcnt = len(rdnorms)
        segdx = rm.randrange(segcnt)
        leadcorner = corners[segdx]
        seglen = fu.distance(corners[segdx+1],leadcorner)
        segnorm = rdnorms[segdx]
        segtang = fu.normalize(fu.v1_v2(leadcorner,corners[segdx+1]))

        minblen = 20
        minbwid = 20
        maxblen = int(min([self.max_building_length, 2*seglen]))
        maxbwid = self.max_building_width
        squat = 0.5
        rmfact = self.max_floor_count/(squat*flcnt) + 1

        if rdrtside:
            sidepitch = -np.pi
            sidebase = -1.0*rdwidth
            #sidebase = -1.0*rdwidth/2.0
            easementsign = -1.0
        else:
            sidepitch = 0
            sidebase = 1.0*rdwidth
            #sidebase = 1.0*rdwidth/2.0
            easementsign = 1.0
        rdpitch = fu.angle_from_xaxis(segtang)
        #rdpitch = fu.angle_from_xaxis(segtang) - sidepitch
        #rdpitch = np.pi/6

        def get_random():
            blen = rm.randrange(max([int(maxblen/rmfact),minblen]),maxblen)
            rmfactored = int(maxbwid/rmfact)
            widbottom = max([rmfactored,minbwid])
            bwid = min([rm.randrange(widbottom,maxbwid), blen*2])

            #sidesoff = blen if rdrtside else 0
            sidesoff = 0
            #easement = int((bwid+0.5)/2.0)*easementsign +\
            #    rm.randrange(0,2+int(blen/2.0))*easementsign + sidebase
            easement = int((bwid+0.5)/2.0)*easementsign + sidebase
            #easement = 0
            base = fu.translate_vector(fu.translate_vector(leadcorner[:],
                fu.scale_vector(segnorm[:],[easement,easement,easement])),
                fu.scale_vector(segtang[:],[sidesoff,sidesoff,sidesoff]))
            #base = [50,50,0]
            bhei = 10
            #stry = rm.randrange(int(-1.0*blen), int(seglen + blen))
            stry = seglen/2
            #stry = 0
            xtry,ytry,ztry = fu.translate_vector(base[:],
                fu.scale_vector(segtang[:],[stry,stry,stry]))
            corners = self.make_corners(xtry,ytry,ztry,blen,bwid,bhei,rdpitch)
            boxtry = bbox(position = [xtry,ytry,ztry], corners = corners)
            return boxtry,blen,bwid,bhei

        try_cnt = 0
        max_tries = 50
        tries_exceeded = False
        boxtry,blen,bwid,bhei = get_random()
        while boxtry.intersects(bboxes, boxtry) and not tries_exceeded:
        #while boxtry.intersects([], boxtry) and not tries_exceeded:
            try_cnt += 1
            tries_exceeded = try_cnt == max_tries
            boxtry,blen,bwid,bhei = get_random()
        if tries_exceeded:return False,None,None,None,None
        x, y, z = boxtry.position
        ang_z = rdpitch
        return [x, y, z], blen, bwid, bhei, ang_z
        
    def make_corners(self,x,y,z,l,w,h,theta):
        hl = l/2.0
        hw = w/2.0
        corners = [[-hl,-hw,0],[hl,-hw,0],[hl,hw,0],[-hl,hw,0]]
        #corners = [[0,0,0],[l,0,0],[l,w,0],[0,w,0]]
        fu.rotate_z_coords(corners,theta)
        fu.translate_coords(corners,[x,y,z])
        return corners

    def get_building_floor_count(self, *args, **kwargs):
        mflc = self.max_floor_count
        rmfact = 4
        flcnt = rm.randrange(int(mflc/rmfact),mflc)
        if flcnt == 0: return 1
        return flcnt

class city(node):

    def __init__(self, *args, **kwargs):
        chils = self.make_primitives(*args, **kwargs)
        self._default_('children',chils,**kwargs)
        node.__init__(self, *args, **kwargs)

    def make_blocks_from_roads(self, *args, **kwargs):
        road_system_ = args[0]
        elements = []
        bl_themes = {
            #'suburbs' : (20,3,30,20), 
            #'residential' : (10,10,60,60), 
            #'park' : (3,1,10,10), 
            #'commercial' : (20,20,100,100), 
            'industrial' : (20,6,80,80), 
                }
        themes = [ke for ke in bl_themes.keys()]
        print('theeeemes',bl_themes)
        print('theeeemes',themes)

        roads = road_system_.roads
        bboxes = road_system_.get_bbox()
        blcnt = 0
        blocks = []
        for rd in roads:
            blbc,blfc,blbl,blbw = bl_themes[rm.choice(themes)]
            elements.append(block(name = 'block_' + str(blcnt + 1), 
                building_count = blbc, max_floor_count = blfc, 
                max_building_length = blbl, max_building_width = blbw, 
                road = rd, side = 'right',bboxes = bboxes))
            blocks.append(elements[-1])
            #blbc,blfc,blbl,blbw = bl_themes[rm.choice(themes)]
            blcnt += 1
            elements.append(block(name = 'block_' + str(blcnt + 1), 
                building_count = blbc, max_floor_count = blfc, 
                max_building_length = blbl, max_building_width = blbw, 
                road = rd, side = 'left',bboxes = bboxes))
            blocks.append(elements[-1])
            blcnt += 1
        self.blocks = blocks
        return elements

    def make_primitives(self, *args, **kwargs):
        if 'road_system' in kwargs.keys():
            road_system_ = kwargs['road_system']
        else:
            rsargs = {
                #'seeds':[[0,-1000,0],[1000,0,0],[-1000,0,0],[0,1000,0]], 
                'seeds':[[0,0,0],[1000,0,0],[0,1000,0]], 
                'region_bounds':[(-2000,2000),(-2000,2000)], 
                'intersection_count':10, 
                'linkmin':200, 
                'linkmax':400, 
                    }
            road_system_ = road_system(**rsargs)

        self.road_system = road_system_
        parts = [
            road_system_, 
                ] + self.make_blocks_from_roads(road_system_)
        return parts

    def get_bbox(self):
        return self.road_system.get_bbox()









