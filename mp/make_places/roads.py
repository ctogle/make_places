import make_places.fundamental as fu
import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv
import make_places.primitives as pr
#from make_places.fundamental import element
from make_places.scenegraph import node
from make_places.floors import floor
from make_places.primitives import arbitrary_primitive
from make_places.primitives import ucube
from make_places.primitives import uoctagon
#from make_places.primitives import unit_cube
import make_places.pkler as pk

import os, pdb
import numpy as np
import random as rm
from math import sqrt
from math import cos
from math import sin
from math import tan
from copy import deepcopy as dcopy

cardinal_directions = [
    'north', 'northeast', 
    'east', 'southeast', 
    'south', 'southwest', 
    'west', 'northwest']
cardinal_norms = [
    cv.yhat.copy(),cv.vector(1,1,0).normalize(),
    cv.xhat.copy(),cv.vector(1,-1,0).normalize(),
    cv.yhat.copy().flip(),cv.vector(-1,-1,0).normalize(),
    cv.xhat.copy().flip(),cv.vector(-1,1,0).normalize()]

class vehicle_primitive(arbitrary_primitive):
    vehiclexml = os.path.join(pr.primitive_data_path, 'truck.mesh.xml') 
    offset = cv.zero()

    def __init__(self, *args, **kwargs):
        pvehdata = pr.primitive_data_from_xml(self.vehiclexml)
        arbitrary_primitive.__init__(self, *args, **pvehdata)
        self._default_('tag','_vehicle_',**kwargs)
        self._scale_uvs_ = False
        self.translate(self.offset)

class truck_primitive(vehicle_primitive):
    vehiclexml = os.path.join(pr.primitive_data_path, 'truck.mesh.xml')

class taxi_primitive(vehicle_primitive):
    vehiclexml = os.path.join(pr.primitive_data_path, 'Body.mesh.xml')
    offset = cv.vector(0,0,0.5)

class car_batch(node):

    possible_vehicles = [truck_primitive,taxi_primitive]

    def __init__(self, *args, **kwargs):
        self._default_('cargs',[],**kwargs)
        self._default_('consumes_children',True,**kwargs)
        self._default_('grit_renderingdistance',100,**kwargs)
        self._default_('grit_lod_renderingdistance',2000,**kwargs)
        self.primitives = self.make_batch(self.cargs)
        node.__init__(self, *args, **kwargs)

    def make_batch(self, cargs):
        cars = []
        for cgs in cargs:
            new = rm.choice(self.possible_vehicles)()
            new.rotate_z(cgs['rotation'].z)
            new.translate(cgs['position'])
            cars.append(new)
        return cars

clip_length = 25
class intersection(node):
    def __init__(self, *args, **kwargs):
        #self._default_('consumes_children',True,**kwargs)
        self._default_('grit_renderingdistance',1000,**kwargs)
        self._default_('grit_lod_renderingdistance',2000,**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('road_width',20,**kwargs)
        self._default_('road_height',2,**kwargs)
        self.primitives = self.make_segments(*args, **kwargs)
        #children = self.place_vehicles()
        children = []
        self.add_child(*children)
        node.__init__(self, *args, **kwargs)

    def find_corners(self):
        v1 = cv.vector( clip_length, clip_length*tan(fu.to_rad(22.5)),0)
        v2 = cv.vector( clip_length,-clip_length*tan(fu.to_rad(22.5)),0)
        v3 = cv.vector(-clip_length, clip_length*tan(fu.to_rad(22.5)),0)
        v4 = cv.vector(-clip_length,-clip_length*tan(fu.to_rad(22.5)),0)
        v5 = cv.vector( clip_length*tan(fu.to_rad(22.5)), clip_length,0)
        v6 = cv.vector(-clip_length*tan(fu.to_rad(22.5)), clip_length,0)
        v7 = cv.vector( clip_length*tan(fu.to_rad(22.5)),-clip_length,0)
        v8 = cv.vector(-clip_length*tan(fu.to_rad(22.5)),-clip_length,0)
        corners = [v1, v2, v3, v4, v5, v6, v7, v8]
        return corners

    def terrain_points(self):
        # i need the location of the octagon verts!
        #rh2 = self.road_height/2.0
        rh2 = 0.4
        corners = self.find_corners()
        center = cv.center_of_mass(corners).translate_z(-0.5)
        #mpu.translate_vector(center,[0,0,-0.5])
        corners = mpu.dice_edges(corners, dices = 1)
        corners.append(center)
        position = self.tform.true().position
        cv.translate_coords(corners,position.copy().translate_z(-rh2))
        return corners

    def place_vehicles(self, cnt = 2):
        rotz1 = rm.randrange(12) * fu.to_rad(30.0)
        rotz2 = rm.randrange(12) * fu.to_rad(30.0)
        rotz3 = rm.randrange(12) * fu.to_rad(30.0)
        trargs1 = {
            'position':cv.zero(), 
            'rotation':cv.vector(0,0,rotz1), 
                }
        trargs2 = {
            'position':cv.vector(10,10,0), 
            'rotation':cv.vector(0,0,rotz2), 
                }
        trargs3 = {
            'position':cv.vector(-10,-10,0), 
            'rotation':cv.vector(0,0,rotz3), 
                }
        trk_batch = car_batch(parent = self, 
            cargs = [trargs1,trargs2,trargs3])
        return [trk_batch]

    def make_segments(self, *args, **kwargs):
        segs = []
        #rw = self.road_width
        rh = self.road_height
        octang = 22.5
        clipln = clip_length
        octscl = clipln / cos(fu.to_rad(octang))
        uo = uoctagon()
        uo.scale(cv.vector(octscl,octscl,rh))
        rh = 0.25
        uo.translate_z(-rh-2.0)
        #uo.translate_face([0,0,-rh],'top')
        segs.append(uo)
        return segs
        
    def get_bbox(self):
        corners = self.find_corners()
        #corners = [[0,0,0],[50,0,0],[50,50,0],[0,50,0]]
        #fu.rotate_z_coords(corners,theta)
        position = self.tform.true().position
        cv.translate_coords(corners,position)
        bboxes = [mpbb.bbox(corners = corners)]
        #bboxes = [fu.bbox(corners = corners)]
        return bboxes

class road_segment_primitive(arbitrary_primitive):
    roadxml = os.path.join(pr.primitive_data_path, 'road.mesh.xml')

    def __init__(self, *args, **kwargs):
        proaddata = pr.primitive_data_from_xml(self.roadxml)
        arbitrary_primitive.__init__(self, *args, **proaddata)
        self.coords_by_face = self.find_faces()
        self.tag = '_road_'
        self._scale_uvs_ = False

    def find_faces(self):
        fronts = [v for v in self.coords if v.y < 0.0]
        backs = [v for v in self.coords if v.y > 0.0]
        lefts = [v for v in self.coords if v.x < 0.0]
        rights = [v for v in self.coords if v.x > 0.0]
        bottoms = [v for v in self.coords if v.z <= 0.0]
        tops = [v for v in self.coords if v.z > 0.0]
        facedict = {
            'front':fronts, 
            'back':backs, 
            'left':lefts,                                        
            'right':rights, 
            'top':tops, 
            'bottom':bottoms, 
                }
        return facedict

    def translate_face(self, vect, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        cv.translate_coords(face_coords, vect)
        self.calculate_normals()
        self.modified = True

    def rotate_z_face(self, ang_z, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        foff = cv.center_of_mass(face_coords)
        cv.translate_coords(face_coords, cv.flip(foff))
        cv.rotate_z_coords(face_coords, ang_z)
        cv.translate_coords(face_coords, foff)
        self.calculate_normals()
        self.modified = True

class highway_segment_primitive(road_segment_primitive):
    roadxml = os.path.join(pr.primitive_data_path, 'highroad.mesh.xml')

class road(node):
    road_prim_type = road_segment_primitive

    def __init__(self, *args, **kwargs):
        kwargs['uv_scales'] = cv.one()
        self._default_('uv_tform',
            self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('grit_renderingdistance',1000,**kwargs)
        self._default_('grit_lod_renderingdistance',2000,**kwargs)
        self._default_('consumes_children',True,**kwargs)
        self._default_('road_width', 10, **kwargs)
        self._default_('road_height', 1, **kwargs)
        self.clip_length = clip_length
        self.set_segmented_vertices(*args, **kwargs)
        self.set_corners(self.segmented_vertices)
        segs = self.make_segments(*args, **kwargs)
        litter = self.litter(segs)
        self.primitives = segs + litter
        node.__init__(self, *args, **kwargs)

    def pick_seg_count(self, vs):
        ds = cv.distance(vs[0],vs[-1])
        seglen = 15
        return int(ds/seglen)

    def litter(self, segs):
        lit = []
        return lit

    def terrain_points(self):
        tpts = []
        for corns in self.corners:
            tcorns = corns[:]
            cv.translate_coords_z(corns[:],-0.25)
            tcorns = mpu.dice_edges(tcorns, dices = 1)
            mcorns = [tcorns[3],tcorns[7]]
            cv.translate_coords_z(mcorns,-0.25)
            tpts.extend([tc for tc in tcorns if not tc in tpts])
        return tpts
        
    def set_corners(self, verts):
        corners = []
        vcnt = len(verts)
        for sgdx in range(1,vcnt):            
            p1,p2 = verts[sgdx-1],verts[sgdx]
            corns = self.make_corners(p1,p2)
            corners.append(corns)
        self.corners = corners

    def make_corners(self, p1, p2):
        widt = self.road_width
        
        p1_p2 = cv.v1_v2(p1,p2)
        leng = cv.magnitude(p1_p2)
        p1_p2.normalize()
        
        ang_z = cv.angle_from_xaxis_xy(p1_p2)
        corns = [
            cv.vector(0,-widt/2.0,0),
            cv.vector(leng,-widt/2.0,0),
            cv.vector(leng,widt/2.0,0),
            cv.vector(0,widt/2.0,0)]
        cv.rotate_z_coords(corns,ang_z)
        cv.translate_coords(corns,p1)
        cv.translate_coords_z(corns[1:3],p2.z-p1.z)
        return corns

    def get_bbox(self):
        bboxes = []
        for corns in self.corners:
            bboxes.append(mpbb.bbox(corners = corns))
            #bboxes.append(fu.bbox(corners = corns))
        return bboxes

    def get_cardinal_normals(self, dirs):
        def getcardnorm(dx):
            cardx = cardinal_directions.index(dirs[dx])
            cardn = cardinal_norms[cardx]
            return cardn
        norms = [getcardnorm(x) for x in range(2)]
        return norms

    def info_from_topology(self, *args, **kwargs):
        topol = kwargs['topology']
        nodes = kwargs['nodes']
        st,en = topol[nodes[0]],topol[nodes[1]]
        stp = st['inter']['position']
        enp = en['inter']['position']
        return stp, enp

    def set_segmented_vertices(self, *args, **kwargs):
        kweys = kwargs.keys()
        if 'topology' in kweys:
            stp, enp = self.info_from_topology(*args, **kwargs)
        else:
            stp = kwargs['start']
            enp = kwargs['end']
        dirs = kwargs['directions']
        norms = self.get_cardinal_normals(dirs)
        self.stnorm = norms[0].copy()
        self.ednorm = norms[1].copy().flip()

        segdice = True
        verts = [stp,enp]
        verts = self.clip_tips(verts,norms[0],norms[1])
        verts = self.add_tips(verts,norms[0],norms[1])

        scnt = self.pick_seg_count(verts)
        self.segment_count = scnt
        def bend(vs):
            tips = vs[:2] + vs[-2:]
            #cox,coy,coz = [list(i) for i in zip(*tips)]
            cox = [t.x for t in tips]
            coy = [t.y for t in tips]
            coz = [t.z for t in tips]
            #cox,coy,coz = [list(i) for i in zip(*tips)]
            tim = [0.0,1.0,2.0,3.0]
            alpha = 1.0/2.0
            mpu.parameterize_time(tips,tim,alpha)
            cox = mpu.catmull_rom(cox,tim,scnt)
            coy = mpu.catmull_rom(coy,tim,scnt)
            coz = mpu.catmull_rom(coz,tim,scnt)
            new = [cv.vector(*i) for i in zip(cox,coy,coz)]
            return new

        if segdice: verts = bend(verts)
        self.segmented_vertices = verts
        return verts

    def add_tips(self,verts,n1,n2):
        clip = 25
        v1 = verts[0].copy()
        v2 = verts[1].copy()
        cl1,cl2 = clip,clip
        v1.translate(n1.copy().scale_u(cl1))
        v2.translate(n2.copy().scale_u(cl2))
        #mpu.translate_vector(v1,mpu.scale_vector(n1[:],[cl1,cl1,cl1]))
        #mpu.translate_vector(v2,mpu.scale_vector(n2[:],[cl2,cl2,cl2]))
        verts.extend([v1, v2])
        verts.append(verts.pop(-3))
        return verts

    def clip_tips(self,verts,n1,n2):
        cl = self.clip_length
        v1 = verts[0].copy().translate(n1.copy().scale_u(cl))
        v2 = verts[-1].copy().translate(n2.copy().scale_u(cl))
        #v1 = mpu.translate_vector(verts[0][:],
        #    mpu.scale_vector(n1[:],[cl,cl,cl]))
        #v2 = mpu.translate_vector(verts[-1][:],
        #    mpu.scale_vector(n2[:],[cl,cl,cl]))
        verts[0] = v1
        verts[-1] = v2
        #verts[1] = v2
        return verts

    def make_segments(self, *args, **kwargs):
        verts = self.segmented_vertices
        rw = self.road_width
        rh = self.road_height
        segments = []
        vcnt = len(verts)
        tangs = [self.stnorm.copy().xy().normalize()]
        angs = []
        for sgdx in range(1,vcnt):            
            p1,p2 = verts[sgdx-1],verts[sgdx]
            tangs.append(cv.v1_v2(p1,p2).xy().normalize())
            #tangs.append(cv.v1_v2(p1,p2).normalize())
            #tangs.append(mpu.normalize(mpu.v1_v2(p1,p2)))
        tangs.append(self.ednorm.copy().xy().normalize())
        for tgdx in range(1,vcnt+1):
            t1,t2 = tangs[tgdx-1],tangs[tgdx]
            a12 = cv.angle_between_xy(t1,t2)
            sign = 0.0 if a12 == 0.0 else a12/abs(a12)
            if abs(a12) > np.pi/2:
                a12 = 0.0
            angs.append(sign * abs(a12))
        legs = [True]*vcnt
        legs[1::2] = [False]*(int(vcnt/2))
        for sgdx in range(1,vcnt):            
            a1,a2 = angs[sgdx-1],angs[sgdx]
            p1,p2 = verts[sgdx-1],verts[sgdx]
            strips = self.make_segment(p1,p2,rw,rh,a1,a2,legs[sgdx])
            #segments.append(strip)
            segments.extend(strips)
        return segments

    def make_segment(self, p1, p2, widt, depth, a1, a2, leg = False):
        leng = cv.distance_xy(p1,p2)
        p1_p2 = cv.v1_v2(p1,p2).xy().normalize()
        #p1_p2 = cv.v1_v2(p1,p2).normalize()
        #p1_p2 = mpu.normalize(mpu.v1_v2(p1,p2))
        zdiff = p2.z - p1.z
        ang_z = cv.angle_from_xaxis_xy(p1_p2)
        #strip = ucube()
        strip = self.road_prim_type()#road_segment_primitive()
        #strip = road_segment_primitive()
        strip.scale(cv.vector(leng,widt,depth))
        strip.scale_uvs(cv.vector(leng/widt,1,1))
        strip.translate(cv.vector(leng/2.0,0,-depth))
        strip.rotate_z(ang_z)
        theta1 = -1.0*a1/2.0
        theta2 =      a2/2.0
        strip.rotate_z_face(theta1, 'left')
        strip.translate_face(cv.vector(0,0,zdiff), 'right')
        strip.rotate_z_face(theta2, 'right')
        strip.translate(p1)
        return [strip]

class road_system(node):
    def __init__(self, *args, **kwargs):
        self._default_('name','road_system',**kwargs)
        self._default_('reuse',False,**kwargs)
        self._default_('linkmin', 200, **kwargs)
        self._default_('linkmax', 400, **kwargs)
        self._default_('linkangles', 
            [90*x for x in range(4)], **kwargs)
        self._default_('growth_tips', 5, **kwargs)
        self._default_('region_bounds',[(0,1000),(0,1000)],**kwargs)
        self._default_('seeds',[cv.zero(),cv.vector(1000,1000,0)],**kwargs)
        self._default_('intersection_count',20,**kwargs)
        rwidth = 2*clip_length*tan(fu.to_rad(22.5))
        self._default_('road_width', rwidth, **kwargs)
        #kwargs['road_width'] = rwidth
        children = self.reusing(*args, **kwargs)
        if not children:children = self.children_from_kwargs(*args,**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self.add_child(*children)
        node.__init__(self, *args, **kwargs)

    def children_from_kwargs(self, *args, **kwargs):
        rwidth = self.road_width
        if 'interargs' in kwargs.keys():
            interargs = kwargs['interargs']
            children = self.make_system_from_intersections(interargs,rwidth)
        else: children = self.make_primitives_web(*args, **kwargs)
        return children

    # will be class specific
    def children_from_reuse_file(self, info_file_name):
        info_file_name = os.path.join(os.getcwd(),info_file_name)
        self.reuse_data = pk.load_pkl(info_file_name)
        #self.reuse_data = {'rargs':[],'iargs':[],'topology':None}
        elements = []
        self.roads = []
        for ig in self.reuse_data['iargs']:
            elements.append(intersection(**ig))
        for rarg in self.reuse_data['rargs']:
            newrd = road(**rarg)
            self.roads.append(newrd)
            elements.append(newrd)
        self.topology = self.reuse_data['topology']
        return elements

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
        #pts = [ch.tform.true().position for ch in self.children]
        pts = []
        [pts.extend(ch.owner.terrain_points()) 
            for ch in self.tform.children]
        return pts

    def make_primitives_web(self, *args, **kwargs):
        def good_dir(tip, ang):
            link = rm.choice(range(linkmin,linkmax,50))
            #link = rm.randrange(linkmin,linkmax)
            tippos = tip['position'].copy()
            #angrad = (np.pi/180.0)*ang
            angrad = fu.to_rad(ang)
            z_off_min = -25
            z_off_max =  25
            z_offset = rm.randrange(z_off_min, z_off_max)
            offset = cv.vector(link*cos(angrad),link*sin(angrad),z_offset)
            tippos.translate(offset)
            #newtip = mpu.translate_vector(tippos, offset)
            if not mpu.in_region(region_bounds, tippos):
                return False,None
            for ipos in [i['position'] for i in interargs]:
                d = cv.distance(tippos, ipos)
                if d < linkmin: return False,None
            return True,tippos
            #newtip = mpu.translate_vector(tippos, offset)
            #if not mpu.in_region(region_bounds, newtip):
            #    return False,None
            #for ipos in [i['position'] for i in interargs]:
            #    d = mpu.distance(newtip, ipos)
            #    if d < linkmin: return False,None
            #return True,newtip

        def get_angle(tip):
            nodes = [i['position'] for i in interargs]
            cmass = cv.center_of_mass(nodes)
            #cmass = [np.mean([s[0] for s in nodes]), np.mean([s[1]
            #    for s in nodes]), np.mean([s[2] for s in nodes])]
            #cmass = [0,0,0]
            cmass_ang = fu.to_deg(cv.angle_from_xaxis(
                cv.v1_v2(tip['position'],cmass)))
            tangs = angs[:]
            angdists = [abs(x-cmass_ang) for x in tangs]
            closestang = tangs[angdists.index(min(angdists))]
            tangs.extend([closestang]*20)
            while len(tangs) > 0:
                angdx = rm.randrange(len(tangs))
                ang = tangs.pop(angdx)
                passes,newpos = good_dir(tip, ang)
                if passes:
                    return ang,newpos
            return None,None

        def place_inter(tip):
            ang,newpos = get_angle(tip)
            if ang is None: return
            return newpos

        growth_tips = self.growth_tips
        region_bounds = self.region_bounds
        linkmin, linkmax = self.linkmin,self.linkmax
        seeds = self.seeds
        angs = self.linkangles
        intercnt = self.intersection_count
        seedcnt = len(seeds)
        branches = []
        for idx in range(seedcnt):
            branches.append([{
                'position' : seeds[idx],   
                    }])
        interargs = [br[0] for br in branches]
        sealevelvals = []
        for idx in range(intercnt):
            tips = [br[-min([len(interargs),growth_tips]):] 
                    for br in branches]
            bdx = rm.randrange(seedcnt)
            tip = rm.choice(tips[bdx])
            newpos = place_inter(tip)
            if not newpos is None:
                sealevelvals.append(newpos.z)
                interargs.append({
                    'position' : newpos, 
                        })
                branches[bdx].append(interargs[-1])
            else: print('cant place intersection!!')
        #rwidth = kwargs['road_width']
        rwidth = self.road_width
        self._suggested_sea_level_ = self.pick_sea_level(sealevelvals)
        return self.make_system_from_intersections(interargs, rwidth)

    def pick_sea_level(self, vals):
        maxval = max(vals)
        minval = min(vals)
        rng = maxval - minval
        return minval + rng/10.0

    def make_system_from_intersections(self, interargs, rwidth):
        elements = []
        topology = [{} for inter in interargs]
        for inter, topo in zip(interargs, topology):
            for card in cardinal_directions:
                topo[card] = None
            topo['inter'] = inter
            topo['roads'] = []
            topo['linkcnt'] = 0

        self.reuse_data = {'rargs':[],'iargs':[],'topology':None}
        self.roads = []
        self.highways = []
        for tdx, topo in enumerate(topology):
            topology[tdx] = find_neighbors(topology,topo,rwidth)
        rdbbs = []
        hwbbs = []
        for tdx, topo in enumerate(topology):
            inter = topo['inter']
            inter['topology'] = topology
            inter['topodex'] = tdx
            self.reuse_data['iargs'].append(inter)
            elements.append(intersection(**inter))
            for rarg in topo['roads']:
                self.reuse_data['rargs'].append(rarg)
                newrd = road(**rarg)
                newbb = newrd.get_bbox()
                if not mpbb.intersects(rdbbs,newbb):
                    rdbbs.extend(newbb)
                    self.roads.append(newrd)
                    elements.append(newrd)
                else:
                    newrd = highway(**rarg)
                    newbb = newrd.get_bbox()
                    if not mpbb.intersects(hwbbs,newbb):
                        hwbbs.extend(newbb)
                        self.highways.append(newrd)
                        elements.append(newrd)
                        print('topology mistake from road intersection!')
        self.topology = topology
        self.reuse_data['topology'] = topology
        return elements

    def make_primitives_from_blocks_______(self, *args, **kwargs):
        prims = []
        # given a list of blocks, determine a set of roads which bounds them
        # assume them do not overlap, and that a road should bound each
        # determine locations of intersections as all corners of every block
        # determine the width, length, and position of each road connecting
        # intersections
        # also assume that intersections will never intersect by construction
        #  that is the blocks are sized/positioned to prevent strange
        #  intersections
        # create the kwargs which includes them all
        def get_inter_length():
            return 40
        def get_inter_width():
            return 40
        blocks = args[0]
        used_bcorners = []
        corner_signs = [(-1,-1), (0, -1), (0, 0), (-1, 0)]
        interargs = []
        for bl in blocks:
            corn = bl.corners
            c1, c2, c3, c4 = corn
            for c_, signs in zip(corn, corner_signs):
                ilength = get_inter_length()
                iwidth = get_inter_width()
                ipos = mpu.translate_vector(c_[:], 
                    [signs[0]*ilength,signs[1]*iwidth,0]), 
                if not ipos in used_bcorners:
                    used_bcorners.append(ipos)
                    interargs.append({
                        'name' : 'intersection_' + str(len(used_bcorners)), 
                        'position' : mpu.translate_vector(
                            c_[:],[signs[0]*ilength,signs[1]*iwidth,0]), 
                        'length' : ilength, 
                        'width' : iwidth, 
                        'floor_height' : 1.0})
        return self.make_system_from_intersections(interargs)

    def get_bbox(self):
        bboxes = []
        roads = self.tform.children
        for rdtf in roads:
            rdboxes = rdtf.owner.get_bbox()
            bboxes.extend(rdboxes)
        return bboxes

class highway(road):
    road_prim_type = highway_segment_primitive

    def terrain_points(self):
        tpts = [l.translate_z(5) for l in self.leg_positions]
        #tpts = [mpu.translate_vector(l,[0,0,5]) 
        #        for l in self.leg_positions]
        return tpts
        
    def make_segments(self, *args, **kwargs):
        self.leg_positions = []
        scnt = self.segment_count
        sverts = self.segmented_vertices
        self.sverts_ground = self.segmented_vertices[:]
        #sverts[1][2] += 1
        #sverts[-2][2] += 1
        tim = [0.0,1.0,2.0,3.0]
        alpha = 1.0/2.0
        tips = sverts[:2] + sverts[-2:]
        #tips = sverts[1:3] + sverts[-3:-1]
        coz = [t.z for t in tips]
        mpu.parameterize_time(tips,tim,alpha)
        coz = mpu.catmull_rom(coz,tim,scnt)
        for sv,co in zip(sverts[1:-1],coz): sv.z = min(co,sv.z+20)
        rdsegs = road.make_segments(self, *args, **kwargs)
        return rdsegs

    def make_leg(self, v):
        leg = pr.ucube()
        leg_leng = 20
        leg.scale(cv.vector(5,5,leg_leng))
        leg_pos = v.copy().translate_z(-leg_leng-2.0)
        #leg_pos = [v[0],v[1],v[2]-leg_leng-2.0]
        leg.translate(leg_pos)
        self.leg_positions.append(leg_pos)
        return leg

    def make_segment(self, p1, p2, widt, depth, a1, a2, leg = False):
        depth = 8 # unacceptable...
        rs = road.make_segment(self,p1,p2,widt,depth,a1,a2)
        [r.translate_z(1.75) for r in rs]# unacceptable...
        # use a bbox check to decide to place a leg or not
        if not leg: return rs
        leg = self.make_leg(p1)
        rs.append(leg)
        return rs

def pick_closest(pots,ndists):
    if pots:
        ndx = ndists.index(min(ndists))
        return pots[ndx]
    return None,None

def select_outlet(outlets,ordered):
    for ord_ in ordered:
        if ord_ in outlets:
            return ord_

def north_check(topology,topo,seek_fov,linkmax):
    antidirs = ['west','southwest','south','southeast','east']
    tpos = topo['inter']['position']
    potentials = []
    ndists = []
    tthresh = 50
    max_slope = 0.25
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos.y < pnpos.y:
                ndist = float(pnpos.y - tpos.y)
                
                zdiff = abs(tpos.z - pnpos.z)
                slope = zdiff/abs(ndist)
                if slope > max_slope: continue

                if ndist < linkmax:
                    tdist = float(pnpos.x - tpos.x)
                    pn_fov_theta = fu.to_deg(np.arctan(abs(tdist)/ndist))
                    if pn_fov_theta < seek_fov/2.0:
                        if abs(tdist) <= tthresh:
                            order = ['south','southeast','southwest']
                        elif tdist < -tthresh:
                            order = ['southeast','south','east']
                        elif tdist > tthresh:
                            order = ['southwest','south','west']
                        dir_ = select_outlet(outlets,order)
                        if not dir_ is None:
                            potentials.append((pntopo,dir_))
                            ndists.append(ndist)
    return pick_closest(potentials,ndists)

def south_check(topology,topo,seek_fov,linkmax):
    antidirs = ['west','northwest','north','northeast','east']
    tpos = topo['inter']['position']
    potentials = []
    ndists = []
    tthresh = 50
    max_slope = 0.25
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos.y > pnpos.y:
                ndist = -1*float(pnpos.y - tpos.y)
                zdiff = abs(tpos.z - pnpos.z)
                slope = zdiff/abs(ndist)
                if slope > max_slope: continue
                if ndist < linkmax:
                    tdist = float(pnpos.x - tpos.x)
                    pn_fov_theta = fu.to_deg(np.arctan(abs(tdist)/ndist))
                    if pn_fov_theta < seek_fov/2.0:
                        if abs(tdist) <= tthresh:
                            order = ['north','northeast','northwest']
                        elif tdist < -tthresh:
                            order = ['northeast','north','east']
                        elif tdist > tthresh:
                            order = ['northwest','north','west']
                        dir_ = select_outlet(outlets,order)
                        if not dir_ is None:
                            potentials.append((pntopo,dir_))
                            ndists.append(ndist)
    return pick_closest(potentials,ndists)

def east_check(topology,topo,seek_fov,linkmax):
    antidirs = ['north','northwest','west','southwest','south']
    tpos = topo['inter']['position']
    potentials = []
    ndists = []
    tthresh = 50
    max_slope = 0.25
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos.x < pnpos.x:
                ndist = float(pnpos.x - tpos.x)
                zdiff = abs(tpos.z - pnpos.z)
                slope = zdiff/abs(ndist)
                if slope > max_slope: continue
                if ndist < linkmax:
                    tdist = float(pnpos.y - tpos.y)
                    pn_fov_theta = fu.to_deg(np.arctan(abs(tdist)/ndist))
                    if pn_fov_theta < seek_fov/2.0:
                        if abs(tdist) <= tthresh:
                            order = ['west','southwest','northwest']
                        elif tdist < -tthresh:
                            order = ['northwest','west','north']
                        elif tdist > tthresh:
                            order = ['southwest','west','south']
                        dir_ = select_outlet(outlets,order)
                        if not dir_ is None:
                            potentials.append((pntopo,dir_))
                            ndists.append(ndist)
    return pick_closest(potentials,ndists)

def west_check(topology,topo,seek_fov,linkmax):
    antidirs = ['north','northeast','east','southeast','south']
    tpos = topo['inter']['position']
    potentials = []
    ndists = []
    normdx = 0
    trandx = 1
    tthresh = 50
    max_slope = 0.25
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos.x > pnpos.x:
                ndist = -1*float(pnpos.x - tpos.x)
                zdiff = abs(tpos.z - pnpos.z)
                slope = zdiff/abs(ndist)
                if slope > max_slope: continue
                if ndist < linkmax:
                    tdist = float(pnpos.y - tpos.y)
                    pn_fov_theta = fu.to_deg(np.arctan(abs(tdist)/ndist))
                    if pn_fov_theta < seek_fov/2.0:
                        if abs(tdist) <= tthresh:
                            order = ['east','southeast','northeast']
                        elif tdist < -tthresh:
                            order = ['northeast','east','north']
                        elif tdist > tthresh:
                            order = ['southeast','east','south']
                        dir_ = select_outlet(outlets,order)
                        if not dir_ is None:
                            potentials.append((pntopo,dir_))
                            ndists.append(ndist)
    return pick_closest(potentials,ndists)

neighbor_checks = {
    'north' : north_check, 
    'east' : east_check, 
    'south' : south_check, 
    'west' : west_check, 
        }
def find_neighbors(topology,topo,rwidth):
    topoid = [t is topo for t in topology].index(True)
    seek_fov = 60
    maxlinks = 4
    linkmax = 1000
    for card in cardinal_directions:
        if topo['linkcnt'] >= maxlinks: return topo
        if not card in neighbor_checks.keys(): continue
        neighb,neighbdir = neighbor_checks[card](
            topology,topo,seek_fov,linkmax)
        if not neighb is None:
            topodx = [n is neighb for n in topology].index(True)
            if neighb['linkcnt'] >= maxlinks: continue
            if topodx in topo.values(): continue
            topo[card] = topodx
            topo['linkcnt'] += 1
            neighb[neighbdir] = topoid
            neighb['linkcnt'] += 1
            topo['roads'].append({
                'road_width' : rwidth, 
                'topology' : topology, 
                'directions' : (card,neighbdir), 
                'nodes' : (topoid,topodx)})
    return topo

def no_road_intersects(topology,idx1,idx2):
    topo1 = topology[idx1]
    topo2 = topology[idx2]
    s1 = (topo1['inter']['position'],
          topo2['inter']['position'],)
    cardinals = ['north', 'south', 'east', 'west']
    for x in topology:
        links = [x[key] for key in cardinals if not x[key] is None]
        for ldx in links:
            y = topology[ldx]
            s2 = (x['inter']['position'],
                  y['inter']['position'],)
            if mpu.segments_intersect(s1,s2): return False
    return True
    




