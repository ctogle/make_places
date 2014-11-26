import make_places.fundamental as fu
import mp_utils as mpu
import mp_bboxes as mpbb
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.waters as mpw
from make_places.scenegraph import node
from make_places.roads import road_system
from make_places.roads import highway
from make_places.buildings import building
from make_places.terrain import terrain
import make_places.pkler as pk

from math import sqrt
import numpy as np
import random as rm
import os

class block(node):

    bl_themes = {
        'suburbs' : (30,3,30,30), 
        'residential' : (20,10,70,70), 
        #'park' : (3,1,10,10), 
        'commercial' : (20,20,100,100), 
        'industrial' : (30,6,60,60), 
            }
    themes = [ke for ke in bl_themes.keys()]

    def __init__(self, *args, **kwargs):
        self._default_('name',None,**kwargs)
        self._default_('tform',
            self.def_tform(*args,**kwargs),**kwargs)
        bth = rm.choice(self.themes)
        self._default_('reuse',False,**kwargs)
        self._default_('theme',bth,**kwargs)
        blbc,blfc,blbl,blbw = self.bl_themes[self.theme]
        self._default_('max_floor_count',blfc,**kwargs)
        self._default_('max_building_length',blbl,**kwargs)
        self._default_('max_building_width',blbw,**kwargs)
        self._default_('building_count',blbc,**kwargs)
        children = self.reusing(*args, **kwargs)
        if not children: children =\
            self.children_from_kwargs(*args, **kwargs)
        self.add_child(*children)
        node.__init__(self, *args, **kwargs)

    def children_from_kwargs(self, *args, **kwargs):
        if 'road' in kwargs.keys():
            rd = kwargs['road']
            if not issubclass(rd.__class__,highway):
                children = self.make_buildings_from_road(*args, **kwargs)
            else: children = []
        else:
            pos = kwargs['position']
            length = kwargs['length']
            width = kwargs['width']
            self.corners = self.find_corners(pos, length, width)
            children = self.make_buildings(*args, **kwargs)
        return children

    def children_from_reuse_file(self, info_file_name):
        info_file_name = os.path.join(os.getcwd(),info_file_name)
        self.reuse_data = pk.load_pkl(info_file_name)
        buildings = []
        bcnt = self.reuse_data['bcnt']
        for blarg in self.reuse_data['blargs']:
            buildings.append(building(**blarg))
        self.buildings = buildings
        return buildings

    def output_reuse_file(self, info_file_name):
        info_file_name = os.path.join(os.getcwd(),info_file_name)
        pk.save_pkl(self.reuse_data, info_file_name)

    def reusing(self, *args, **kwargs):
        if not self.reuse or not self.name: return
        info_file_name = '.'.join([self.name,'reusable','data','pkl'])
        if not pk.file_exists(info_file_name):
            chds = self.children_from_kwargs(*args, **kwargs)
            self.output_reuse_file(info_file_name)
            return chds
        else:
            chds = self.children_from_reuse_file(info_file_name)
            return chds

    def terrain_points(self):
        pts = []
        if hasattr(self,'buildings'):
            [pts.extend(bg.terrain_points()) for bg in self.buildings]
        return pts

    def get_bbox(self):
        return self.bboxes

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
        thats = [mpu.normalize(mpu.v1_v2(corns[dx],corns[dx-1])) 
                for dx in range(1,corncnt)]
        rdnorms = [mpu.cross(that,zhat) for that in thats]
        bcnt = self.building_count
        #bcnt = 10
        buildings = []
        reuse_data = {'bcnt':bcnt, 'blargs':[]}
        for bdx in range(bcnt):
            bname = 'building_' + str(bdx)
            flcnt = self.get_building_floor_count()
            bpos,blen,bwid,bhei,ang =\
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
                    'floor_height':0.5, 
                    'ceiling_height':0.5, 
                    'wall_width':0.4, 
                    'wall_height':4.0, 
                    'floors':flcnt, 
                    'rotation':[0,0,ang], 
                        }
                reuse_data['blargs'].append(blarg)
                buildings.append(building(**blarg))
                bboxes.extend(buildings[-1].get_bbox())
        self.buildings = buildings
        self.reuse_data = reuse_data
        self.bboxes = bboxes
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
        seglen = mpu.distance(corners[segdx+1],leadcorner)
        segnorm = rdnorms[segdx]
        segtang = mpu.normalize(mpu.v1_v2(leadcorner,corners[segdx+1]))

        minblen = 20
        minbwid = 20
        maxblen = int(min([self.max_building_length, 2*seglen]))
        maxbwid = self.max_building_width
        squat = 0.5
        rmfact = self.max_floor_count/(squat*flcnt) + 1

        if rdrtside:
            sidepitch = -np.pi
            #sidebase = -1.0*rdwidth
            sidebase = -1.0*rdwidth/2.0
            easementsign = -1.0
        else:
            sidepitch = 0
            #sidebase = 1.0*rdwidth
            sidebase = 1.0*rdwidth/2.0
            easementsign = 1.0
        rdpitch = fu.angle_from_xaxis(segtang)
        #rdpitch = fu.angle_from_xaxis(segtang) - sidepitch
        #rdpitch = np.pi/6

        def get_random():
            blen_bottom = max([int(maxblen/rmfact),minblen])
            blen_top = maxblen
            if blen_bottom >= blen_top: blen_bottom = blen_top - 1
            blen = rm.randrange(blen_bottom,blen_top)
            #blen = rm.randrange(max([int(maxblen/rmfact),minblen]),maxblen)
            rmfactored = int(maxbwid/rmfact)
            widbottom = max([rmfactored,minbwid])
            bwid = min([rm.randrange(widbottom,maxbwid), blen*2])

            #sidesoff = blen if rdrtside else 0
            sidesoff = 0.0
            easement = int((bwid+0.5)/2.0)*easementsign +\
                rm.randrange(2,15 +int(blen/2.0))*easementsign + sidebase
            #easement = int((bwid+0.5)/2.0)*easementsign + sidebase
            #easement = 0
            base = mpu.translate_vector(mpu.translate_vector(leadcorner[:],
                mpu.scale_vector(segnorm[:],[easement,easement,easement])),
                mpu.scale_vector(segtang[:],[sidesoff,sidesoff,sidesoff]))
            #base = [50,50,0]
            bhei = 10.0
            #stry = rm.randrange(int(-1.0*blen), int(seglen + blen))
            stry = rm.randrange(0, int(seglen))
            #stry = seglen/2
            #stry = 0
            xtry,ytry,ztry = mpu.translate_vector(base[:],
                mpu.scale_vector(segtang[:],[stry,stry,stry]))
            corners = self.make_corners(xtry,ytry,ztry,blen,bwid,bhei,rdpitch)
            boxtry = mpbb.bbox(position = [xtry,ytry,ztry], corners = corners)
            return boxtry,blen,bwid,bhei

        try_cnt = 0
        max_tries = 50
        tries_exceeded = False
        boxtry,blen,bwid,bhei = get_random()
        while mpbb.intersects(bboxes, boxtry) and not tries_exceeded:
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
        mpu.rotate_z_coords(corners,theta)
        mpu.translate_coords(corners,[x,y,z])
        return corners

    def get_building_floor_count(self, *args, **kwargs):
        mflc = self.max_floor_count
        rmfact = 4
        flcnt = rm.randrange(int(mflc/rmfact),mflc)
        if flcnt == 0: return 1
        return flcnt

class city(node):

    def __init__(self, *args, **kwargs):
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        children = self.make_city_parts(*args,**kwargs)
        self.add_child(*children)
        node.__init__(self, *args, **kwargs)

    def make_blocks_from_roads(self, *args, **kwargs):
        road_system_ = args[0]
        elements = []
        roads = road_system_.roads
        bboxes = road_system_.get_bbox()
        blcnt = 0
        blocks = []
        for rd in roads:
            elements.append(block(name = 'block_' + str(blcnt + 1), 
                road = rd, side = 'right',bboxes = bboxes,parent = self))
            blocks.append(elements[-1])
            #blbc,blfc,blbl,blbw = bl_themes[rm.choice(themes)]
            lasttheme = elements[-1].theme
            blcnt += 1
            elements.append(block(name = 'block_' + str(blcnt + 1), 
                theme = lasttheme, parent = self, 
                road = rd, side = 'left',bboxes = bboxes))
            blocks.append(elements[-1])
            blcnt += 1
        self.blocks = blocks
        self.bboxes = bboxes
        return elements

    def make_terrain(self, *args, **kwargs):
        kwargs['parent'] = self
        kwargs['splits'] = 8
        kwargs['smooths'] = 5
        kwargs['bboxes'] = self.bboxes
        ter = terrain(**kwargs)
        return [ter]

    def make_road_system(self, *args, **kwargs):
        if 'road_system' in kwargs.keys():
            road_sys = kwargs['road_system']
        else:
            rsargs = {
                'name':'road_system', 
                'seeds':[[0,-1000,0],[1000,0,0],[-1000,0,0],[0,1000,0]], 
                #'seeds':[[0,0,0],[1000,0,0],[0,1000,0]], 
                'region_bounds':[(-1000,1000),(-1000,1000)], 
                'intersection_count':20, 
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
        terra = self.make_terrain(pts_of_interest = pts_of_int, 
                region_bounds = road_sys[0].region_bounds)
        ocean = [mpw.waters(position = [500,500,0],depth = 10,
            sealevel = 0.0,length = 2000,width = 2000)]
        parts = road_sys + blocks + terra + ocean
        return parts

    def get_bbox(self):
        print 'citys bbox requested!!!'
        pdb.set_trace()
        return self.road_system.get_bbox()

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






