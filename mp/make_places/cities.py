import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.waters as mpw
from make_places.scenegraph import node
from make_places.roads import road_system
from make_places.roads import highway
#from make_places.buildings import building
from make_places.buildings import newbuilding as building
from make_places.terrain import terrain
import make_places.pkler as pk

import mp_vector as cv
import mp_utils as mpu
import mp_bboxes as mpbb

from math import sqrt
import numpy as np
import random as rm
import os

class block(node):

    bl_themes = {
        'suburbs' : {
            'max_buildings' : 30,
            'max_floors' : 3, 
            'min_length' : 30, 
            'min_width' : 30, 
            'max_length' : 60, 
            'max_width' : 100, 
                }, 
        'residential' : {
            'max_buildings' : 20,
            'max_floors' : 10, 
            'min_length' : 30, 
            'min_width' : 30, 
            'max_length' : 100, 
            'max_width' : 100, 
                }, 
        'commercial' : {
            'max_buildings' : 10,
            'max_floors' : 30, 
            'min_length' : 40, 
            'min_width' : 40, 
            'max_length' : 100, 
            'max_width' : 100, 
                }, 
        'industrial' : {
            'max_buildings' : 30,
            'max_floors' : 6, 
            'min_length' : 40, 
            'min_width' : 40, 
            'max_length' : 80, 
            'max_width' : 80, 
                }, 
            }
    themes = [ke for ke in bl_themes.keys()]

    def __init__(self, *args, **kwargs):
        self._default_('name',None,**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('reuse',False,**kwargs)

        bth = rm.choice(self.themes)
        self.theme_data = self.bl_themes[bth]

        self._default_('theme',bth,**kwargs)

        children = self.make_children(*args, **kwargs)
        self.add_child(*children)
        node.__init__(self, *args, **kwargs)

    def make_children(self, *args, **kwargs):
        rd = kwargs['road']
        if not issubclass(rd.__class__,highway):
            children = self.make_buildings_from_road(*args, **kwargs)
        else: children = []
        return children

    def terrain_points(self):
        pts = []
        if hasattr(self,'buildings'):
            [pts.extend(bg.terrain_points()) for bg in self.buildings]
        return pts

    def get_bbox(self):
        pbd.set_trace()
        return self.bboxes

    def make_buildings_from_road(self, *args, **kwargs):
        bboxes = kwargs['bboxes']
        rd = kwargs['road']
        rdside = kwargs['side']

        # this info should be prestored on the roads
        corns = rd.segmented_vertices
        corncnt = len(corns)
        zhat = cv.zhat
        thats = [cv.v1_v2(corns[dx],corns[dx-1]).normalize()  
                for dx in range(1,corncnt)]
        rdnorms = [cv.cross(that,zhat) for that in thats]

        bcnt = self.theme_data['max_buildings']
        buildings = []

        for bdx in range(bcnt):
            bname = 'building_' + str(bdx)

            flcnt = self.get_building_floor_count()

            bpos,blen,bwid,ang =\
                self.get_building_position_from_road(
                    corns,rdnorms,flcnt,side = rdside, 
                    road = rd,bboxes = bboxes)

            if not bpos is False:
                blarg = {
                    'theme':self.theme, 
                    'name':bname, 
                    'parent':self, 
                    'position':bpos, 
                    'length':blen, 
                    'width':bwid, 
                    'floors':flcnt, 
                    'rotation':cv.vector(0,0,ang), 
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

        segcnt = len(rdnorms)
        segdx = rm.randrange(segcnt)
        leadcorner = corners[segdx]
        seglen = cv.distance(corners[segdx+1],leadcorner)

        segtang = cv.v1_v2(leadcorner,corners[segdx+1]).normalize()
        rdpitch = cv.angle_from_xaxis(segtang)
        segnorm = rdnorms[segdx].copy()
        if kwargs['side'] == 'right':
            segnorm.flip()
            rdpitch += fu.PI

        minblen = self.theme_data['min_length']
        minbwid = self.theme_data['min_width']
        maxblen = self.theme_data['max_length']
        maxbwid = self.theme_data['max_width']

        def get_random():
            blen = rm.randrange(minblen,maxblen)
            bwid = rm.randrange(minbwid,maxbwid)

            d_to_road = rm.randrange(bwid)
            d_to_road = mpu.clamp(d_to_road,int((bwid+0.5)/2.0),bwid)
            stry = rm.randrange(int(seglen))

            base = leadcorner.copy()
            base.translate(segnorm.copy().scale_u(d_to_road))
            base.translate(segtang.copy().scale_u(stry))

            postry = base
            corners = mpu.make_corners(postry,blen,bwid,rdpitch)
            boxtry = [mpbb.bbox(corners = corners)]
            return boxtry,postry,blen,bwid

        try_cnt = 0
        max_tries = 50
        tries_exceeded = False
        boxtry,boxpos,blen,bwid = get_random()
        while mpbb.intersects(bboxes, boxtry) and not tries_exceeded:
            try_cnt += 1
            tries_exceeded = try_cnt == max_tries
            boxtry,boxpos,blen,bwid = get_random()

        if tries_exceeded:
            #print 'tries exceeded!'
            return False,None,None,None
        else:
            #print 'accepted!',boxpos,blen,bwid
            return boxpos, blen, bwid, rdpitch

    def get_building_floor_count(self, *args, **kwargs):
        mflc = self.theme_data['max_floors']
        flcnt = rm.randrange(int(mflc/4.0),mflc)
        flcnt = int(mpu.clamp(flcnt,1,mflc))
        return flcnt

class city(node):

    def __init__(self, *args, **kwargs):
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        children = self.make_city_parts(*args,**kwargs)
        self.add_child(*children)
        node.__init__(self, *args, **kwargs)

    def make_blocks_from_roads(self, *args, **kwargs):
        road_system_ = args[0]
        roads = road_system_.roads
        bboxes = road_system_.get_bbox()

        blcnt = 0
        blocks = []
        for rd in roads:
            blocks.append(block(name = 'block_' + str(blcnt + 1), 
                road = rd, side = 'right',bboxes = bboxes,parent = self))
            lasttheme = blocks[-1].theme
            blcnt += 1

            blocks.append(block(name = 'block_' + str(blcnt + 1), 
                theme = lasttheme, parent = self, 
                road = rd, side = 'left',bboxes = bboxes))
            blcnt += 1

        self.blocks = blocks
        self.bboxes = bboxes
        return blocks

    def make_terrain(self, *args, **kwargs):
        kwargs['parent'] = self
        kwargs['splits'] = 7
        kwargs['smooths'] = 100
        kwargs['bboxes'] = self.bboxes
        ter = terrain(**kwargs)
        return [ter]

    def make_road_system(self, *args, **kwargs):
        if 'road_system' in kwargs.keys():
            road_sys = kwargs['road_system']
        else:
            rsargs = {
                'name':'road_system', 
                'seeds':[
                    cv.vector(0,-1000,0),
                    cv.vector(1000,0,0),
                    cv.vector(-1000,0,0),
                    cv.vector(0,1000,0)], 
                #'seeds':[[0,-1000,0],[1000,0,0],[-1000,0,0],[0,1000,0]], 
                #'seeds':[[0,0,0],[1000,0,0],[0,1000,0]], 
                'region_bounds':[(-1000,1000),(-1000,1000)], 
                'intersection_count':100, 
                'linkmin':200, 
                'linkmax':400, 
                'parent':self, 
                    }
            road_sys = road_system(**rsargs)
        self.road_system = road_sys
        return [road_sys]

    def make_city_parts(self, *args, **kwargs):
        road_sys = self.make_road_system(*args, **kwargs)
        blocks = self.make_blocks_from_roads(road_sys[0])
        pts_of_int = road_sys[0].terrain_points()
        for bl in blocks: pts_of_int.extend(bl.terrain_points())
        sea_level = road_sys[0]._suggested_sea_level_
        terra = self.make_terrain(sealevel = sea_level, 
            pts_of_interest = pts_of_int, 
            region_bounds = road_sys[0].region_bounds)
        ocean = [mpw.waters(position = cv.zero(),depth = 20,
                sealevel = sea_level,length = 4000,width = 4000)]
        parts = road_sys + blocks + terra + ocean
        return parts

class hashima(city):

    hashimawallsxml = os.path.join(
        pr.primitive_data_path, 'hashima_walls.mesh.xml')

    def __init__(self, *args, **kwargs):
        city.__init__(self, *args, **kwargs)

    def make_city_parts(self, *args, **kwargs):

        walls = pr.primitive_data_from_xml(self.hashimawallsxml)
        wallnode = sg.node(name = 'walls_of_hashima', 
            primitives = [walls])

        #kwargs['parent'] = wallnode
        # decide interargs from walls
        # set block themes from location on island
        # somehow generate terrain to fit wall

        #road_sys = self.make_road_system(*args, **kwargs)
        #blocks = self.make_blocks_from_roads(road_sys)
        #pts_of_int = road_sys.terrain_points()
        #for bl in blocks: pts_of_int.extend(bl.terrain_points())
        #terra = self.make_terrain(pts_of_interest = pts_of_int, 
        #        region_bounds = road_sys.region_bounds)
        #parts = road_sys + blocks + terra

        parts = [wallnode]
        return parts






