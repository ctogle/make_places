import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.waters as mpw
import make_places.newnewroads as nrds
import make_places.buildings as blg
import make_places.newterrain as mtr
import make_places.pkler as pk

import mp_vector as cv
import mp_utils as mpu
import mp_bboxes as mpbb

import matplotlib.pyplot as plt
from math import sqrt
import numpy as np
import random as rm
import pdb
import os

class block(sg.node):

    bl_themes = {
        'suburbs' : {
            'max_buildings' : 40,
            'max_floors' : 3, 
            'min_length' : 30, 
            'min_width' : 30, 
            'max_length' : 50, 
            'max_width' : 70, 
                }, 
        'residential' : {
            'max_buildings' : 30,
            'max_floors' : 10, 
            'min_length' : 30, 
            'min_width' : 30, 
            'max_length' : 80, 
            'max_width' : 80, 
                }, 
        'commercial' : {
            'max_buildings' : 20,
            'max_floors' : 30, 
            'min_length' : 40, 
            'min_width' : 40, 
            'max_length' : 80, 
            'max_width' : 80, 
                }, 
        'industrial' : {
            'max_buildings' : 40,
            'max_floors' : 6, 
            'min_length' : 40, 
            'min_width' : 40, 
            'max_length' : 60, 
            'max_width' : 60, 
                }, 
            }
    themes = [ke for ke in bl_themes.keys()]

    def __init__(self, *args, **kwargs):
        self._default_('name',None,**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('reuse',False,**kwargs)

        bth = rm.choice(self.themes)
        self._default_('theme',bth,**kwargs)
        self.theme_data = self.bl_themes[self.theme]

        children = self.make_buildings_from_road(*args, **kwargs)
        self.add_child(*children)
        sg.node.__init__(self, *args, **kwargs)

    def terrain_points(self):
        pts = []
        if hasattr(self,'buildings'):
            [pts.extend(bg.terrain_points()) for bg in self.buildings]
        return pts

    def terrain_holes(self):
        pts = []
        if hasattr(self,'buildings'):
            [pts.extend(bg.terrain_holes()) for bg in self.buildings]
        return pts

    def get_bbox(self):
        pbd.set_trace()
        return self.bboxes

    def make_buildings_from_road(self, *args, **kwargs):
        bboxes = kwargs['bboxes']
        rd = kwargs['road']
        rdside = kwargs['side']

        corns = rd.vertices
        zhat = cv.zhat
        thats = rd.tangents
        rdnorms = [that.cross(zhat).normalize() for that in thats]

        bcnt = self.theme_data['max_buildings']
        buildings = []

        if rd.style == 'interstate': bcnt = 0
        if blg._building_count_ >= 500: bcnt = 0

        for bdx in range(bcnt):
            flcnt = self.get_building_floor_count()
            bpos,blen,bwid,ang =\
                self.get_building_position_from_road(
                    corns,rdnorms,flcnt,side = rdside, 
                    road = rd,bboxes = bboxes)
            if not bpos is False:
                blarg = {
                    'theme':self.theme, 
                    #'name':bname, 
                    'parent':self, 
                    'position':bpos, 
                    'length':blen, 
                    'width':bwid, 
                    'floors':flcnt, 
                    'rotation':cv.vector(0,0,ang), 
                        }

                buildings.append(blg.building(**blarg))
                bboxes.append(buildings[-1].get_bbox())
        self.buildings = buildings
        return buildings

    def get_building_position_from_road(self, 
            corners, rdnorms, flcnt, **kwargs):
        bboxes = kwargs['bboxes']
        road = kwargs['road']
        rdwidth = road.road_width

        segcnt = len(rdnorms) - 1
        segdx = rm.randrange(segcnt)
        leadcorner = corners[segdx]
        rearcorner = corners[segdx+1]
        seglen = cv.distance(rearcorner,leadcorner)

        segtang = cv.v1_v2(leadcorner,corners[segdx+1]).normalize()
        rdpitch = cv.angle_from_xaxis(segtang)
        segnorm = rdnorms[segdx].copy()
        if kwargs['side'] == 'left':
            segnorm.flip()
        if kwargs['side'] == 'right':
            rdpitch += fu.PI

        minblen = self.theme_data['min_length']
        minbwid = self.theme_data['min_width']
        maxblen = self.theme_data['max_length']
        maxbwid = self.theme_data['max_width']

        def get_random():
            blen = rm.randrange(minblen,maxblen)
            bwid = rm.randrange(minbwid,maxbwid)

            d_to_road = rdwidth/2.0 + bwid/2.0 + rm.randrange(int(bwid))
            stry = rm.randrange(int(seglen))

            base = leadcorner.copy()
            base.translate(segnorm.copy().scale_u(d_to_road))
            base.translate(segtang.copy().scale_u(stry))

            postry = base
            corners = mpu.make_corners(postry,blen,bwid,rdpitch)
            boxtry = mpbb.xy_bbox(corners = corners)
            return boxtry,postry,blen,bwid

        try_cnt = 0
        max_tries = 100
        tries_exceeded = False
        boxtry,boxpos,blen,bwid = get_random()

        acceptable = True
        for bb in bboxes:
            isect = boxtry.intersect_xy(bb)
            if isect:
                if [io.bottomlevel for io in isect['other members']].count(True) > 0:
                    acceptable = False

        #if not acceptable:
        #    for bb in bboxes: bb.plot()
        #    boxtry.plot(colors = ['green','blue','purple'])
        #    plt.show()

        while not acceptable and not tries_exceeded:
            try_cnt += 1
            tries_exceeded = try_cnt == max_tries
            boxtry,boxpos,blen,bwid = get_random()

            acceptable = True
            for bb in bboxes:
                isect = boxtry.intersect_xy(bb)
                if isect:
                    if [io.bottomlevel for io in isect['other members']].count(True) > 0:
                        acceptable = False

        print 'tried',try_cnt,'times to place a building'

        global trydatax
        global trydatay
        trydatay.append(try_cnt)
        trydatax.append(len(trydatay))

        if tries_exceeded:return False,None,None,None
        else:return boxpos, blen, bwid, rdpitch

    def get_building_floor_count(self, *args, **kwargs):
        mflc = self.theme_data['max_floors']
        flcnt = rm.randrange(int(mflc/4.0),mflc)
        flcnt = int(mpu.clamp(flcnt,1,mflc))
        return flcnt

trydatax = []
trydatay = []
def plot_try_data():
    global trydatax
    global trydatay
    plt.plot(trydatax,trydatay)
    plt.show()

class acity(sg.node):

    def __init__(self, *args, **kwargs):
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        children = self.make_city_parts(*args,**kwargs)
        self.add_child(*children)
        sg.node.__init__(self, *args, **kwargs)

    def make_blocks_from_roads(self, *args, **kwargs):
        bboxes = self.road_bboxes
        rplans = self.road_system_plans

        blcnt = 0
        blocks = []
        for rd in rplans:
            if not issubclass(rd.__class__,nrds.road_plan):
                print 'skipping',rd
                continue

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
        target_polygon_edge_length = 10
        target_primitive_edge_length = 200
        tkwargs = {
            'parent':self, 
            'fixed_pts':kwargs['pts_of_interest'], 
            'hole_pts':kwargs['hole_pts'], 
            'region_pts':kwargs['region_bounds'], 
            'polygon_edge_length':target_polygon_edge_length, 
            'primitive_edge_length':target_primitive_edge_length, 
                }
        ter = mtr.make_terrain(**tkwargs)
        return [ter]

    def make_road_system(self, *args, **kwargs):
        iplans,rplans = nrds.make_road_system_plans(50)
        rpts = nrds.generate_region_points(iplans,rplans)

        rsysplans = iplans[:]
        rsysplans.extend(rplans)
        self.road_system_plans = rsysplans

        rsys = []
        fpts = []
        hpts = []
        bboxes = []
        for rp in rsysplans:
            bboxes.append(rp.xybb)
            rsys.extend(rp.build())
            fpts.extend(rp.terrain_points())
            hpts.extend(rp.terrain_holes())

        self.road_system = rsys
        self.road_bboxes = bboxes
        return rsys,fpts,hpts,rpts

    def make_city_parts(self, *args, **kwargs):
        road_sys,tpts,hpts,rpts = self.make_road_system(*args, **kwargs)
        #rpts = mpu.make_corners(cv.zero(),2000,2000,0)
        blocks = self.make_blocks_from_roads()
        #blocks = []
        pts_of_int = tpts
        hole_pts = hpts
        for bl in blocks: pts_of_int.extend(bl.terrain_points())
        for bl in blocks: hole_pts.extend(bl.terrain_holes())
        sea_level = -0.3 # road_sys[0]._suggested_sea_level_
        terra = self.make_terrain(sealevel = sea_level, 
            pts_of_interest = pts_of_int, hole_pts = hole_pts, 
            region_bounds = rpts)
        ocean = [mpw.waters(position = cv.zero(),depth = 20,
                sealevel = sea_level,length = 4000,width = 4000)]
        parts = road_sys + blocks + terra + ocean
        return parts

def city():
    bboxes,fpts,hpts,rpts = lay_roads()

def lay_roads():
    iplans,rplans = nrds.make_road_system_plans(50)
    rpts = nrds.generate_region_points(iplans,rplans)

    rsysplans = iplans[:]
    rsysplans.extend(rplans)
    self.road_system_plans = rsysplans

    fpts = []
    hpts = []
    bboxes = []
    for rp in rsysplans:
        gritgeo.create_element(rp.build())
        bboxes.append(rp.xybb)
        fpts.extend(rp.terrain_points())
        hpts.extend(rp.terrain_holes())
    return bboxes,fpts,hpts,rpts

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






