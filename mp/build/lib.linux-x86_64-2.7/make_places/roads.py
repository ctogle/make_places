import make_places.fundamental as fu
import mp_utils as mpu
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
    [0,1,0],fu.normalize([1,1,0]),
    [1,0,0],fu.normalize([1,-1,0]), 
    [0,-1,0],fu.normalize([-1,-1,0]), 
    [-1,0,0],fu.normalize([-1,1,0])]

class truck_primitive(arbitrary_primitive):
    truckxml = os.path.join(pr.primitive_data_path, 'truck.mesh.xml')

    def __init__(self, *args, **kwargs):
        ptruckdata = pr.primitive_data_from_xml(self.truckxml)
        arbitrary_primitive.__init__(self, *args, **ptruckdata)
        self.tag = '_truck_'
        self._scale_uvs_ = False

class car_batch(node):

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
            new = truck_primitive()
            new.rotate_z(cgs['rotation'][2])
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
        children = self.place_vehicles()
        self.add_child(*children)
        node.__init__(self, *args, **kwargs)

    def find_corners(self):
        v1 = [ clip_length, clip_length*tan(fu.to_rad(22.5)),0]
        v2 = [ clip_length,-clip_length*tan(fu.to_rad(22.5)),0]
        v3 = [-clip_length, clip_length*tan(fu.to_rad(22.5)),0]
        v4 = [-clip_length,-clip_length*tan(fu.to_rad(22.5)),0]
        v5 = [ clip_length*tan(fu.to_rad(22.5)), clip_length,0]
        v6 = [-clip_length*tan(fu.to_rad(22.5)), clip_length,0]
        v7 = [ clip_length*tan(fu.to_rad(22.5)),-clip_length,0]
        v8 = [-clip_length*tan(fu.to_rad(22.5)),-clip_length,0]
        corners = [v1, v2, v3, v4, v5, v6, v7, v8]
        return corners

    def terrain_points(self):
        # i need the location of the octagon verts!
        #rh2 = self.road_height/2.0
        rh2 = 0.15
        corners = self.find_corners()
        corners = fu.dice_edges(corners, dices = 1)
        position = self.tform.true().position
        x,y,z = position
        fu.translate_coords(corners,[x,y,z-rh2])
        return corners

    def place_vehicles(self, cnt = 2):
        rotz1 = rm.randrange(12) * fu.to_rad(30.0)
        rotz2 = rm.randrange(12) * fu.to_rad(30.0)
        rotz3 = rm.randrange(12) * fu.to_rad(30.0)
        trargs1 = {
            'position':[0,0,0], 
            'rotation':[0,0,rotz1], 
                }
        trargs2 = {
            'position':[10,10,0], 
            'rotation':[0,0,rotz2], 
                }
        trargs3 = {
            'position':[-10,-10,0], 
            'rotation':[0,0,rotz3], 
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
        uo.scale([octscl,octscl,rh])
        uo.translate([0,0,-rh])
        segs.append(uo)
        return segs
        
    def get_bbox(self):
        corners = self.find_corners()
        #corners = [[0,0,0],[50,0,0],[50,50,0],[0,50,0]]
        #fu.rotate_z_coords(corners,theta)
        position = self.tform.true().position
        x,y,z = position
        fu.translate_coords(corners,[x,y,z])
        bboxes = [fu.bbox(corners = corners)]
        return bboxes

def catmull_rom(P,T,tcnt):
    spl = P[:1]
    for j in range(1, len(P)-2):  # skip the ends
        for t in range(tcnt):  # t: 0 .1 .2 .. .9
            tt = float(t)/tcnt
            tt = T[1] + tt*(T[2]-T[1])
            p = spline([P[j-1], P[j], P[j+1], P[j+2]],
                    [T[j-1], T[j], T[j+1], T[j+2]],tt)
            spl.append(p)
    spl.extend(P[-2:])
    return spl

def spline(p,time,t):
    L01 = p[0] * (time[1] - t) / (time[1] - time[0]) + p[1] * (t - time[0]) / (time[1] - time[0])
    L12 = p[1] * (time[2] - t) / (time[2] - time[1]) + p[2] * (t - time[1]) / (time[2] - time[1])
    L23 = p[2] * (time[3] - t) / (time[3] - time[2]) + p[3] * (t - time[2]) / (time[3] - time[2])
    L012 = L01 * (time[2] - t) / (time[2] - time[0]) + L12 * (t - time[0]) / (time[2] - time[0])
    L123 = L12 * (time[3] - t) / (time[3] - time[1]) + L23 * (t - time[1]) / (time[3] - time[1])
    C12 = L012 * (time[2] - t) / (time[2] - time[1]) + L123 * (t - time[1]) / (time[2] - time[1])
    return C12

class road_segment_primitive(arbitrary_primitive):
    roadxml = os.path.join(pr.primitive_data_path, 'road.mesh.xml')

    def __init__(self, *args, **kwargs):
        proaddata = pr.primitive_data_from_xml(self.roadxml)
        arbitrary_primitive.__init__(self, *args, **proaddata)
        self.coords_by_face = self.find_faces()
        self.tag = '_road_'
        self._scale_uvs_ = False

    def find_faces(self):
        fronts = [v for v in self.coords if v[1] < 0.0]
        backs = [v for v in self.coords if v[1] > 0.0]
        lefts = [v for v in self.coords if v[0] < 0.0]
        rights = [v for v in self.coords if v[0] > 0.0]
        bottoms = [v for v in self.coords if v[2] <= 0.0]
        tops = [v for v in self.coords if v[2] > 0.0]
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
        fu.translate_coords(face_coords, vect)
        self.calculate_normals()
        self.modified = True

    def rotate_z_face(self, ang_z, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        foff = mpu.center_of_mass(face_coords)
        fu.translate_coords(face_coords, fu.flip(foff))
        fu.rotate_z_coords(face_coords, ang_z)
        fu.translate_coords(face_coords, foff)
        self.calculate_normals()
        self.modified = True

class road(node):
    def __init__(self, *args, **kwargs):
        kwargs['uv_scales'] = [1,1,1]
        self._default_('uv_tform',
            self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('grit_renderingdistance',1000,**kwargs)
        self._default_('grit_lod_renderingdistance',2000,**kwargs)
        self._default_('road_width', 10, **kwargs)
        self._default_('road_height', 1, **kwargs)
        self.clip_length = clip_length
        self.set_segmented_vertices(*args, **kwargs)
        self.set_corners(self.segmented_vertices)
        segs = self.make_segments(*args, **kwargs)
        litter = self.litter(segs)
        self.primitives = segs + litter
        node.__init__(self, *args, **kwargs)

    def litter(self, segs):
        lit = []
        return lit

    def terrain_points(self):
        tpts = []
        
        for corns in self.corners:
            tcorns = fu.translate_coords(corns[:],[0,0,-0.25])
            tcorns = fu.dice_edges(tcorns, dices = 1)
            mcorns = [tcorns[3],tcorns[7]]
            fu.translate_coords(mcorns,[0,0,-0.25])
            tpts.extend([tc for tc in tcorns if not tc in tpts])
            
        return tpts
        
        '''#
        verts = self.segmented_vertices
        vcnt = len(verts)
        for sgdx in range(1,vcnt):
            p1,p2 = verts[sgdx-1],verts[sgdx]
            tcorns = fu.translate_coords(
                self.make_corners(p1,p2),[0,0,-0.25])
            tcorns = fu.dice_edges(tcorns, dices = 1)
            tpts.extend(tcorns)
            #tpts.append(fu.translate_vector(
            #    mpu.center_of_mass(tpts),[0,0,-1.5]))
            tpts.append(mpu.center_of_mass(tpts))
            mcorns = [tpts[3],tpts[7],tpts[8]]
            fu.translate_coords(mcorns,[0,0,-0.25])
        #return fu.uniq(tpts)
        return tpts
        '''#

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
        
        p1_p2 = fu.v1_v2(p1,p2)
        leng = fu.magnitude(p1_p2)
        p1_p2 = fu.normalize(p1_p2)
        
        ang_z = fu.angle_from_xaxis(p1_p2)
        corns = [[0,-widt/2.0,0],[leng,-widt/2.0,0],
                [leng,widt/2.0,0],[0,widt/2.0,0]]
        fu.rotate_z_coords(corns,ang_z)
        fu.translate_coords(corns,p1)
        fu.translate_coords(corns[1:3],[0,0,p2[2]-p1[2]])
        return corns

    def get_bbox(self):
        bboxes = []
        for corns in self.corners:
            bboxes.append(fu.bbox(corners = corns))
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
        self.stnorm = norms[0]
        self.ednorm = fu.flip(norms[1])

        segdice = True
        verts = [stp,enp]
        verts = self.clip_tips(verts,norms[0],norms[1])
        verts = self.add_tips(verts,norms[0],norms[1])

        def parameterize_time(points,time,alpha):
            total = 0
            for idx in range(1,4):
                v1v2 = fu.v1_v2(points[idx-1],points[idx])
                total += fu.magnitude(v1v2)**(2.0*alpha)
                time[idx] = total

        def bend(vs):
            tips = vs[:2] + vs[-2:]
            cox,coy,coz = [list(i) for i in zip(*tips)]
            tim = [0.0,1.0,2.0,3.0]
            alpha = 1.0/2.0
            parameterize_time(tips,tim,alpha)
            cox = catmull_rom(cox,tim,10)
            coy = catmull_rom(coy,tim,10)
            coz = catmull_rom(coz,tim,10)
            new = [list(i) for i in zip(cox,coy,coz)]
            return new

        if segdice: verts = bend(verts)
        self.segmented_vertices = verts
        return verts

    def add_tips(self,verts,n1,n2):
        clip = 25
        v1 = verts[0][:]
        v2 = verts[1][:]
        cl1,cl2 = clip,clip
        fu.translate_vector(v1,fu.scale_vector(n1[:],[cl1,cl1,cl1]))
        fu.translate_vector(v2,fu.scale_vector(n2[:],[cl2,cl2,cl2]))
        verts.extend([v1, v2])
        verts.append(verts.pop(-3))
        return verts

    def clip_tips(self,verts,n1,n2):
        cl = self.clip_length
        v1 = fu.translate_vector(verts[0][:],
            fu.scale_vector(n1[:],[cl,cl,cl]))
        v2 = fu.translate_vector(verts[-1][:],
            fu.scale_vector(n2[:],[cl,cl,cl]))
        verts[0] = v1
        verts[1] = v2
        return verts

    def make_segments(self, *args, **kwargs):
        verts = self.segmented_vertices
        rw = self.road_width
        rh = self.road_height
        segments = []
        vcnt = len(verts)
        tangs = [self.stnorm]
        angs = []
        for sgdx in range(1,vcnt):            
            p1,p2 = verts[sgdx-1],verts[sgdx]
            tangs.append(fu.normalize(fu.v1_v2(p1,p2)))
        tangs.append(self.ednorm)
        for tgdx in range(1,vcnt+1):
            t1,t2 = tangs[tgdx-1],tangs[tgdx]
            a12 = fu.angle_between_xy(t1,t2)
            sign = 0.0 if a12 == 0.0 else a12/abs(a12)
            if abs(a12) > np.pi/2:
                a12 = 0.0
            angs.append(sign * abs(a12))
        for sgdx in range(1,vcnt):            
            a1,a2 = angs[sgdx-1],angs[sgdx]
            p1,p2 = verts[sgdx-1],verts[sgdx]
            strips = self.make_segment(p1,p2,rw,rh,a1,a2)
            #segments.append(strip)
            segments.extend(strips)
        return segments

    def make_segment(self, p1, p2, widt, depth, a1, a2):
        leng = fu.distance_xy(p1,p2)
        p1_p2 = fu.normalize(fu.v1_v2(p1,p2))
        zdiff = p2[2] - p1[2]
        ang_z = fu.angle_from_xaxis_xy(p1_p2)
        #strip = ucube()
        strip = road_segment_primitive()
        strip.scale([leng,widt,depth])
        strip.scale_uvs([leng/widt,1,1])
        strip.translate([leng/2.0,0,-depth])
        strip.rotate_z(ang_z)
        theta1 = -1.0*a1/2.0
        theta2 =      a2/2.0
        strip.rotate_z_face(theta1, 'left')
        strip.translate_face([0,0,zdiff], 'right')
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
        self._default_('seeds',[[0,0,0],[1000,1000,0]],**kwargs)
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
            tippos = tip['position'][:]
            angrad = (np.pi/180.0)*ang
            z_off_min = -25
            z_off_max =  25
            z_offset = rm.randrange(z_off_min, z_off_max)
            offset = [link*cos(angrad),link*sin(angrad),z_offset]
            newtip = fu.translate_vector(tippos, offset)
            if not fu.in_region(region_bounds, newtip):
                return False,None
            for ipos in [i['position'] for i in interargs]:
                d = fu.distance(newtip, ipos)
                if d < linkmin: return False,None
            return True,newtip

        def get_angle(tip):
            nodes = [i['position'] for i in interargs]
            cmass = [np.mean([s[0] for s in nodes]), np.mean([s[1]
                for s in nodes]), np.mean([s[2] for s in nodes])]
            #cmass = [0,0,0]
            cmass_ang = fu.to_deg(fu.angle_from_xaxis(
                fu.v1_v2(tip['position'],cmass)))
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
        for idx in range(intercnt):
            tips = [br[-min([len(interargs),growth_tips]):] 
                    for br in branches]
            bdx = rm.randrange(seedcnt)
            tip = rm.choice(tips[bdx])
            newpos = place_inter(tip)
            if not newpos is None:
                interargs.append({
                    'position' : newpos, 
                        })
                branches[bdx].append(interargs[-1])
            else: print('cant place intersection!!')
        #rwidth = kwargs['road_width']
        rwidth = self.road_width
        return self.make_system_from_intersections(interargs, rwidth)

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
        for tdx, topo in enumerate(topology):
            topology[tdx] = find_neighbors(topology,topo,rwidth)
        rdbbs = []
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
                if not fu.bbox.intersects(newbb[0],rdbbs,newbb):
                    rdbbs.extend(newbb)
                    self.roads.append(newrd)
                    elements.append(newrd)
                else:
                    newrd = highway(**rarg)
                    newbb = newrd.get_bbox()
                    rdbbs.extend(newbb)
                    self.roads.append(newrd)
                    elements.append(newrd)
                    print('topology mistake from road intersection!')
        self.topology = topology
        self.reuse_data['topology'] = topology
        return elements

    def make_primitives_from_blocks(self, *args, **kwargs):
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
                ipos = fu.translate_vector(c_[:], 
                    [signs[0]*ilength,signs[1]*iwidth,0]), 
                if not ipos in used_bcorners:
                    used_bcorners.append(ipos)
                    interargs.append({
                        'name' : 'intersection_' + str(len(used_bcorners)), 
                        'position' : fu.translate_vector(
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

    def make_segments(self, *args, **kwargs):
        sverts = self.segmented_vertices
        sverts_ground = self.segmented_vertices[:]
        for sv in sverts[1:-1]: fu.translate_vector(sv,[0,0,10])
        for sv in sverts[2:-2]: fu.translate_vector(sv,[0,0,10])
        rdsegs = road.make_segments(self, *args, **kwargs)
        return rdsegs

    def make_leg(self, v):
        leg = pr.ucube()
        leg_leng = 20
        leg.scale([5,5,leg_leng])
        leg.translate(fu.translate_vector(v[:],[0,0,-leg_leng]))
        return leg

    def make_segment(self, p1, p2, widt, depth, a1, a2):
        rs = road.make_segment(self,p1,p2,widt,depth,a1,a2)
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
    max_slope = 0.5
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos[1] < pnpos[1]:
                ndist = float(pnpos[1] - tpos[1])
                
                zdiff = abs(tpos[2] - pnpos[2])
                slope = zdiff/abs(ndist)
                if slope > max_slope: continue

                if ndist < linkmax:
                    tdist = float(pnpos[0] - tpos[0])
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
    max_slope = 0.5
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos[1] > pnpos[1]:
                ndist = -1*float(pnpos[1] - tpos[1])
                zdiff = abs(tpos[2] - pnpos[2])
                slope = zdiff/abs(ndist)
                if slope > max_slope: continue
                if ndist < linkmax:
                    tdist = float(pnpos[0] - tpos[0])
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
    normdx = 0
    trandx = 1
    tthresh = 50
    max_slope = 0.5
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos[normdx] < pnpos[normdx]:
                ndist = float(pnpos[normdx] - tpos[normdx])
                zdiff = abs(tpos[2] - pnpos[2])
                slope = zdiff/abs(ndist)
                if slope > max_slope: continue
                if ndist < linkmax:
                    tdist = float(pnpos[trandx] - tpos[trandx])
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
    max_slope = 0.5
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos[normdx] > pnpos[normdx]:
                ndist = -1*float(pnpos[normdx] - tpos[normdx])
                zdiff = abs(tpos[2] - pnpos[2])
                slope = zdiff/abs(ndist)
                if slope > max_slope: continue
                if ndist < linkmax:
                    tdist = float(pnpos[trandx] - tpos[trandx])
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
            if fu.segments_intersect(s1,s2): return False
    return True
    




