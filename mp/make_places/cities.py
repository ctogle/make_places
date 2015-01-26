import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.blueprints as mbp
import make_places.waters as mpw
import make_places.newnewroads as nrds
import make_places.buildings as blg
import make_places.newterrain as mtr
import make_places.pkler as pk
import make_places.profiler as prf

import make_places.gritty as gritgeo

import mp_vector as cv
import mp_utils as mpu
import mp_bboxes as mpbb

import cStringIO as sio
import matplotlib.pyplot as plt
from math import sqrt
import numpy as np
import random as rm
import pdb
import os

class newblock(mbp.blueprint):

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

    def terrain_points(self,buildings):
        pts = []
        [pts.extend(bg.terrain_points()) for bg in buildings]
        return pts

    def terrain_holes(self,buildings):
        pts = []
        [pts.extend(bg.terrain_holes()) for bg in buildings]
        return pts

    def _params(self):
        bcnt = self.theme_data['max_buildings']
        minblen = self.theme_data['min_length']
        minbwid = self.theme_data['min_width']
        maxblen = self.theme_data['max_length']
        maxbwid = self.theme_data['max_width']
        return bcnt,minblen,minbwid,maxblen,maxbwid

    def __init__(self,road = None,side = 'left',theme = None):
        mbp.blueprint.__init__(self)
        self.road = road
        self.side = side

        if theme is None: bth = rm.choice(self.themes)
        else: bth = theme
        self.theme = bth
        self.theme_data = self.bl_themes[self.theme]

    def _make(self,bboxes):
        if bboxes is None: bboxes = []
        road,side = self.road,self.side
        tpts,hpts = [],[]
        if not road.style == 'interstate' and blg._building_count_ < 500:
            blnodes = self.buildings_from_road(road,side,bboxes)
            tpts.extend(self.terrain_points(blnodes))
            hpts.extend(self.terrain_holes(blnodes))
            gritgeo.create_element(blnodes)
        return tpts,hpts

    def buildings_from_road(self,rd,rdside,bboxes):
        buildings = []
        bcnt,minblen,minbwid,maxblen,maxbwid = self._params()
        for bdx in range(bcnt):
            flcnt = self.get_building_floor_count()
            bpos,blen,bwid,ang =\
                self.get_building_position_from_road(
                    rd,rdside,bboxes,minblen,minbwid,
                    maxblen,maxbwid)
            if not bpos is False:
                blarg = {'theme':self.theme, 
                    'position':bpos,'length':blen,'width':bwid, 
                    'rotation':cv.vector(0,0,ang),'floors':flcnt}
                buildings.append(blg.building(**blarg))
                bboxes.append(buildings[-1].get_bbox())
        return buildings





    def get_building_position_from_road(self,road,rdside,bboxes,
                                minblen,minbwid,maxblen,maxbwid):
        def check_lot(boxtry):
            for bb in bboxes:
                isect = boxtry.intersect_xy(bb)
                if isect:
                    if [io.bottomlevel for io in isect['other members']].count(True) > 0:
                        return False
            return True

        try_cnt = 0
        max_tries = 100
        tries_exceeded = False
        acceptable = False
        while not acceptable and not tries_exceeded:
            try_cnt += 1
            tries_exceeded = try_cnt == max_tries
            boxtry,bpos,blen,bwid,bpitch = get_random(
                road,rdside,bboxes,minblen,maxblen,minbwid,maxbwid)
            acceptable = check_lot(boxtry)

        print 'tried',try_cnt,'times to place a building'
        if tries_exceeded:return False,None,None,None
        else:return bpos,blen,bwid,bpitch

    def get_building_floor_count(self, *args, **kwargs):
        mflc = self.theme_data['max_floors']
        flcnt = rm.randrange(int(mflc/4.0),mflc)
        flcnt = int(mpu.clamp(flcnt,1,mflc))
        return flcnt

def get_random(road,rdside,bboxes,minblen,maxblen,minbwid,maxbwid):
    rdtangs = road.tangents
    rdnorms = road.normals
    rdwidth = road.total_width
    rdvts = road.vertices
    segcnt = len(rdvts) - 1

    segdx = rm.randrange(segcnt)
    segtang = rdtangs[segdx]
    rdpitch = cv.angle_from_xaxis_xy(segtang)
    segnorm = rdnorms[segdx].copy()
    if rdside == 'left':segnorm.flip()
    if rdside == 'right':rdpitch += fu.PI
    blen = rm.randrange(minblen,maxblen)
    bwid = rm.randrange(minbwid,maxbwid)
    d_to_road = rdwidth/2.0 + bwid/2.0 + rm.randrange(int(bwid))
    base = rdvts[segdx].copy()
    base.translate(segnorm.copy().scale_u(d_to_road))
    corners = mpu.make_corners(base,blen,bwid,rdpitch)
    boxtry = mpbb.xy_bbox(corners = corners)
    return boxtry,base,blen,bwid,rdpitch




def build_block(**buildopts):
    block_factory = newblock(**buildopts)









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

        rd = kwargs['road']
        rdside = kwargs['side']
        bboxes = kwargs['bboxes']
        if not rd.style == 'interstate' and blg._building_count_ < 500:
            children = self.make_buildings_from_road(rd,rdside,bboxes)
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

    def make_buildings_from_road(self,rd,rdside,bboxes):
        buildings = []

        bcnt = self.theme_data['max_buildings']
        minblen = self.theme_data['min_length']
        minbwid = self.theme_data['min_width']
        maxblen = self.theme_data['max_length']
        maxbwid = self.theme_data['max_width']

        for bdx in range(bcnt):
            flcnt = self.get_building_floor_count()
            bpos,blen,bwid,ang =\
                self.get_building_position_from_road(
                    rd,rdside,bboxes,minblen,minbwid,
                    maxblen,maxbwid)
            if not bpos is False:
                blarg = {'parent':self,'theme':self.theme, 
                    'position':bpos,'length':blen,'width':bwid, 
                    'rotation':cv.vector(0,0,ang),'floors':flcnt}
                buildings.append(blg.building(**blarg))
                bboxes.append(buildings[-1].get_bbox())
        self.buildings = buildings
        return buildings

    def get_building_position_from_road(self,road,rdside,bboxes,
                                minblen,minbwid,maxblen,maxbwid):
        rdvts = road.vertices
        rdtangs = road.tangents
        rdnorms = road.normals
        #rdwidth = road.road_width
        rdwidth = road.total_width
        segcnt = len(rdvts) - 1

        def check_lot(boxtry):
            for bb in bboxes:
                isect = boxtry.intersect_xy(bb)
                if isect:
                    if [io.bottomlevel for io in isect['other members']].count(True) > 0:
                        return False
            return True

        def get_random():
            segdx = rm.randrange(segcnt)
            segtang = rdtangs[segdx]
            rdpitch = cv.angle_from_xaxis_xy(segtang)
            segnorm = rdnorms[segdx].copy()
            if rdside == 'left':segnorm.flip()
            if rdside == 'right':rdpitch += fu.PI
            blen = rm.randrange(minblen,maxblen)
            bwid = rm.randrange(minbwid,maxbwid)
            d_to_road = rdwidth/2.0 + bwid/2.0 + rm.randrange(int(bwid))
            base = rdvts[segdx].copy()
            base.translate(segnorm.copy().scale_u(d_to_road))
            corners = mpu.make_corners(base,blen,bwid,rdpitch)
            boxtry = mpbb.xy_bbox(corners = corners)
            return boxtry,base,blen,bwid,rdpitch

        try_cnt = 0
        max_tries = 100
        tries_exceeded = False
        acceptable = False
        while not acceptable and not tries_exceeded:
            try_cnt += 1
            tries_exceeded = try_cnt == max_tries
            boxtry,bpos,blen,bwid,bpitch = get_random()
            acceptable = check_lot(boxtry)

        print 'tried',try_cnt,'times to place a building'
        if tries_exceeded:return False,None,None,None
        else:return bpos,blen,bwid,bpitch

    def get_building_floor_count(self, *args, **kwargs):
        mflc = self.theme_data['max_floors']
        flcnt = rm.randrange(int(mflc/4.0),mflc)
        flcnt = int(mpu.clamp(flcnt,1,mflc))
        return flcnt





def city(road_steps = 2,roads = True,blocks = True,terrain = True,water = True):
    summary = sio.StringIO()
    rplans,iplans,bboxes,fpts,hpts,rpts = [],[],[],[],[],[]
    if roads:
        rplans,iplans,bboxes,fpts,hpts,rpts =\
            lay_roads(rplans,iplans,bboxes,fpts,hpts,rpts,road_steps,summary)
    if blocks:
        rplans,iplans,bboxes,fpts,hpts,rpts =\
            build_blocks_from_roads(rplans,iplans,bboxes,fpts,hpts,rpts,summary)
    if terrain:
        rplans,iplans,bboxes,fpts,hpts,rpts =\
            build_terrain(rplans,iplans,bboxes,fpts,hpts,rpts,summary)
    if water:build_waters(-2.5,summary)
    print summary.getvalue()

def lay_roads(rplans,iplans,bboxes,fpts,hpts,rpts,gsteps,summary):
    summary.write('\nlay_roads:\n')
    summary.write('\t' + str(gsteps) + ' growth steps\n')
    ret,took = prf.measure_time('making road plans',nrds.make_road_system_plans,gsteps)
    summary.write('\tmaking road plans took ')
    summary.write(str(np.round(took,3)))
    summary.write(' seconds\n')

    #iplans,rplans = nrds.make_road_system_plans(gsteps)
    iplans,rplans = ret
    rpts = nrds.generate_region_points(iplans,rplans)
    fpts = []
    hpts = []
    bboxes = []

    def build_plans(plans):
        for rp in plans:
            gritgeo.create_element(rp.build())
            bboxes.append(rp.xybb)
            fpts.extend(rp.terrain_points())
            hpts.extend(rp.terrain_holes())

    build_plans(rplans)
    build_plans(iplans)
    return rplans,iplans,bboxes,fpts,hpts,rpts

def build_blocks_from_roads(rplans,iplans,bboxes,fpts,hpts,rpts,summary):
    blcnt = 0
    for rd in rplans:
        if not issubclass(rd.__class__,nrds.road_plan):continue
        bth = rm.choice(newblock.themes)
        ablock = newblock(**{'road':rd,'side':'right','theme':bth})
        btpts,bhpts = ablock._make(bboxes)
        fpts.extend(btpts)
        hpts.extend(bhpts)
        ablock = newblock(**{'road':rd,'side':'left','theme':bth})
        btpts,bhpts = ablock._make(bboxes)
        fpts.extend(btpts)
        hpts.extend(bhpts)
        blcnt += 2
    return rplans,iplans,bboxes,fpts,hpts,rpts

def build_terrain(rplans,iplans,bboxes,fpts,hpts,rpts,summary):
    summary.write('\nbuild_terrain:\n')
    ter,took = prf.measure_time('generate terrain',mtr.make_terrain,
        fixed_pts = fpts, hole_pts = hpts, region_pts = rpts, 
        polygon_edge_length = 10, primitive_edge_length = 150,
        summary = summary)
    summary.write('\tgenerating terrain took ')
    summary.write(str(np.round(took,3)))
    summary.write(' seconds\n')
    gritgeo.create_element(ter)
    return rplans,iplans,bboxes,fpts,hpts,rpts

def build_waters(sea_level,summary):
    ocean = mpw.waters(position = cv.zero(),depth = 20,
        sealevel = sea_level,length = 4000,width = 4000)
    gritgeo.create_element(ocean)

#################################################################################

def hashima(road_steps = 2,roads = True,blocks = False,terrain = False,water = True):
    summary = sio.StringIO()
    rplans,iplans,bboxes,fpts,hpts,rpts = [],[],[],[],[],[]

    hashimawallsxml = os.path.join(
        pr.primitive_data_path,'hashima_walls.mesh.xml')
    walls = pr.arbitrary_primitive(
        **pr.primitive_data_from_xml(hashimawallsxml))
    walls.scale(cv.one().scale_u(2)).translate_z(-20)
    gritgeo.create_primitive(walls)

    if roads:
        rplans,iplans,bboxes,fpts,hpts,rpts =\
            lay_roads(rplans,iplans,bboxes,fpts,hpts,rpts,road_steps,summary)
    if blocks:
        rplans,iplans,bboxes,fpts,hpts,rpts =\
            build_blocks_from_roads(rplans,iplans,bboxes,fpts,hpts,rpts,summary)
    if terrain:
        rplans,iplans,bboxes,fpts,hpts,rpts =\
            build_terrain(rplans,iplans,bboxes,fpts,hpts,rpts,summary)
    if water:build_waters(-25,summary)
    print summary.getvalue()

#################################################################################



class hashima___(sg.node):

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






