import make_places.fundamental as fu
from make_places.scenegraph import node
from make_places.primitives import arbitrary_primitive
import make_places.profiler as prf

from math import sqrt
from copy import deepcopy as dcopy
import numpy as np
import random as rm
import pdb, time







terrain_numbers = [0]
def get_terrain_number(repeat = False):
    if repeat: return str(terrain_numbers[0] - 1)
    num = terrain_numbers.pop(0)
    nex = num + 1
    terrain_numbers.append(nex)
    return str(num)

class terrain_point(fu.base):

    def __init__(self, *args, **kwargs):
        self._default_('position',[0,0,0],**kwargs)
        self._default_('neighbors',None,**kwargs)
        self._default_('weights',[1,1,1],**kwargs)
        self._str = str((self.position[0],self.position[1]))

    def __add__(self, other):
        newpos = fu.midpoint(self.position,other.position)
        newneighbors = self.neighbors + other.neighbors
        newweights = fu.scale_vector(self.weights[:],other.weights)
        new = terrain_point(
            position = newpos, 
            neighbors = newneighbors, 
            weights = newweights)
        return new

    def relax(self,xstr = 1.0,ystr = 1.0,zstr = 1.0):
        global howmany
        if not len(self.neighbors) in [4,6,2]:
            howmany += 1
            print 'howmany', howmany, len(self.neighbors), self.position
            pdb.set_trace()
        centroid = fu.center_of_mass([v.position for v in self.neighbors])
        wx,wy,wz = self.weights[0],self.weights[1],self.weights[2]
        move = fu.scale_vector(
            fu.v1_v2(self.position,centroid), 
            [xstr*wx,ystr*wy,zstr*wz])
        fu.translate_vector(self.position, move)
        return fu.magnitude(move)

howmany = 0
class terrain_triangle(fu.base):

    def __init__(self, *args, **kwargs):
        self._default_('verts',None,**kwargs)
        self._default_('children',None,**kwargs)
        self._default_('splits',0,**kwargs)
        self.set_center(*args, **kwargs)

    def __str__(self):
        _str = '\n'.join([' v'+str(dx)+' :\t'+\
            str(self.verts[dx].position) for dx in range(3)])
        return _str

    def set_center(self, *args, **kwargs):
        vposs = [v.position for v in self.verts]
        self._default_('center',fu.center_of_mass(vposs),**kwargs)
        self.com_vects = [fu.v1_v2(v,self.center) for v in vposs]
        self.com_vects = [fu.normalize(v) for v in self.com_vects]

    def bisect_all(self, vcnt, controls):
        t1,t2,t3 = self.verts
        newt1 = bisect(t1,t2,vcnt,controls)
        newt2 = bisect(t2,t3,vcnt,controls)
        newt3 = bisect(t3,t1,vcnt,controls)
        newt1.neighbors.extend([newt2,newt3])
        newt2.neighbors.extend([newt3,newt1])
        newt3.neighbors.extend([newt1,newt2])
        return newt1,newt2,newt3

    def fix_topology(self, locs = {}):
        tempkeys = locs.keys()
        if not self.children:
            for vdx,v in enumerate(self.verts):
                str_v = v._str
                if not str_v in tempkeys:
                    locs[str_v] = v
                    tempkeys.append(str_v)
                else:
                    keep = locs[str_v]
                    locnes = [n._str for n in keep.neighbors]
                    [keep.neighbors.append(n) for n in 
                        v.neighbors if not n._str in locnes]
                    self.verts[vdx] = keep
        else:
            for ch in self.children:
                locs = ch.fix_topology(locs = locs)
        return locs
    '''#
    def fix_topology(self, locs = {}):
        tempkeys = locs.keys()
        if not self.children: return locs
        for ch in self.children:
            locs = ch.fix_topology(locs = locs)
            for vdx,v in enumerate(ch.verts):
                str_v = v._str
                if not str_v in tempkeys:
                    locs[str_v] = v
                    tempkeys.append(str_v)
                else:
                    keep = locs[str_v]
                    locnes = [n._str for n in keep.neighbors]
                    [keep.neighbors.append(n) for n in 
                        v.neighbors if not n._str in locnes]
                    ch.verts[vdx] = keep
        return locs
    '''#

    def split(self, vcnt, controls, locs = None):
        if locs is None: locs = {}
        self.splits += 1
        if self.children:
            #[ch.split(vcnt, controls) for ch in self.children[1:]]
            [ch.split(vcnt, controls, locs) for ch in self.children]
            #prf.measure_time('fix topology of terrain', 
            #            self.fix_topology, locs = locs)
        else:
            t1,t2,t3 = self.verts
            newt1,newt2,newt3 = self.bisect_all(vcnt, controls)
            self.children = [
                terrain_triangle(verts = [newt1,newt2,newt3]), 
                terrain_triangle(verts = [t1,newt1,newt3]), 
                terrain_triangle(verts = [t2,newt2,newt1]), 
                terrain_triangle(verts = [t3,newt3,newt2])]
            #prf.measure_time('fix topology of terrain', 
            #            self.fix_topology, locs = locs)
            self.fix_topology(locs = locs)

    def inside(self, pt):
        corners = [fu.translate_vector(v.position[:],tv) 
            for v,tv in zip(self.verts,self.com_vects)]
        return fu.inside(pt, corners)

    def fix_closest(self, pts, locs):
        if not pts: return
        all_verts = locs.values()
        verts = [v.position for v in all_verts]
        for pt in pts:
            if not self.inside(pt): continue
            nearest,neardis,neardex = fu.find_closest_xy(pt,verts)
            closest = all_verts[neardex]
            q2 = pt[2] - closest.position[2]
            closest.position[2] += q2
            newwt = [0.0,0.0,0.0]
            all_verts[neardex].weights = newwt

    def on_boundary(self, v):
        corners = self.verts
        s1 = [corners[0].position,corners[1].position]
        s2 = [corners[1].position,corners[2].position]
        s3 = [corners[2].position,corners[0].position]
        if fu.pt_on_segment(v.position,s1): return True
        elif fu.pt_on_segment(v.position,s2): return True
        elif fu.pt_on_segment(v.position,s3): return True
        else: return False

    def fix_bounds(self, locs):
        all_verts = locs.values()
        bpts = 0
        for uqvt in all_verts:
            if not self.inside(uqvt.position):
                uqvt.weights = [0,0,uqvt.weights[2]]
                bpts += 1
        print 'found',bpts,'boundary points in',len(all_verts),'points'

    def smooth(self, icnt, locs):
        tpoints = locs.values()
        movement = 0.0
        for idx in range(icnt):
            for tp in tpoints:
                movement += tp.relax()
        return movement

    def mesh(self):
        verts = []
        nverts = []
        faces = []
        face_materials = []
        uvs = []
        materials = ['ground']
        data = self.face_data()
        for fdx,fdat in enumerate(data):
            newverts = [dcopy(f.position) for f in fdat]
            v1v2 = fu.v1_v2(newverts[0],newverts[1])
            v1v3 = fu.v1_v2(newverts[0],newverts[2])
            newnorml = [fu.normalize(fu.cross(v1v2,v1v3)) for f in fdat]
            newuvs = [[0,0],[1,0],[0,1]]
            verts.extend(newverts)
            nverts.extend(newnorml)
            uvs.extend(newuvs)
            faces.append([3*fdx+x for x in range(3)])
            face_materials.append(materials[0])
        xmlfile = '.'.join(['terrain',
            str(get_terrain_number()),'mesh','xml'])
        pwargs = {
            'position' : [0,0,0], 
            'verts' : verts, 
            'nverts' : nverts, 
            'uvs' : uvs, 
            'faces' : faces, 
            'materials' : materials, 
            'face_materials' : face_materials, 
            'xmlfilename' : xmlfile, 
                }
        new = arbitrary_primitive(**pwargs)
        new.modified = True
        return new

    def count_vertices(self):
        return 3**(self.splits+1)

    def face_data(self):
        data = []
        if self.children:
            [data.extend(ch.face_data()) for ch in self.children]
        else: data.append(self.verts)
        return data

def bisect(tv1,tv2,vcnt,controls,tolerance = 25,big_tolerance = 250):
    if tv1 in tv2.neighbors and tv2 in tv1.neighbors:
        newpos = fu.midpoint(tv1.position,tv2.position)
        if controls:
            nearest,dist,ndex = fu.find_closest_xy(newpos,controls)
            zdiff = nearest[2] - newpos[2]
            if dist < tolerance: zoff = zdiff
            elif dist < big_tolerance:
                zoff = rm.choice([-1,0,1])*(dist**(1.0/2.0)/vcnt)
            else: zoff = rm.choice([-1,0,1])*(250.0/vcnt)
        else: zoff = rm.choice([-1,0,1])*(1000.0/vcnt)
        newpos[2] += zoff
        newtv = terrain_point(position = newpos)
        newtv.neighbors = [tv1,tv2]
        tv1.neighbors.append(newtv)
        tv2.neighbors.append(newtv)
        tv1.neighbors.remove(tv2)
        tv2.neighbors.remove(tv1)
    else: newtv = [n for n in tv1.neighbors if n in tv2.neighbors][0]
    return newtv

def make_terrain(initial_tps,locs = {},splits = 2,smooths = 25, 
                pts_of_interest = [[250,250,25],[500,250,-25]]):
    pts_of_interest = fu.uniq(pts_of_interest)
    t1 = terrain_point(position = initial_tps[0])
    t2 = terrain_point(position = initial_tps[1])
    t3 = terrain_point(position = initial_tps[2])
    t1.neighbors = [t2,t3]
    t2.neighbors = [t3,t1]
    t3.neighbors = [t1,t2]
    init_verts = [t1,t2,t3]
    terra = terrain_triangle(verts = init_verts)
    #locs = {}
    for ivt in init_verts: locs[ivt._str] = ivt
    for sp in range(splits):
        vcnt = terra.count_vertices()
        prf.measure_time('split terrain', terra.split, vcnt, pts_of_interest, locs)
    prf.measure_time('fix bounds', terra.fix_bounds, locs)
    prf.measure_time('fix closest', terra.fix_closest, pts_of_interest, locs)
    prf.measure_time('smooth terrain', terra.smooth, smooths, locs)
    return terra.mesh()

class terrain(node):
    def __init__(self, *args, **kwargs):
        self._default_('grit_renderingdistance',1000,**kwargs)
        self._default_('grit_lod_renderingdistance',10000,**kwargs)
        self._default_('pts_of_interest',[],**kwargs)
        self._default_('splits',4,**kwargs)
        self._default_('smooths',50,**kwargs)
        self._default_('region_bounds',[(0,1000),(0,1000)],**kwargs)
    
        rb = self.region_bounds
        t1 = [rb[0][0],rb[1][0],0]
        t2 = [rb[0][1],rb[1][0],0]
        t3 = [rb[0][0],rb[1][1],0]
        t4 = [rb[0][1],rb[1][1],0]
        
        #r = 1000
        #t1 = [-r,0,0]
        #t3 = [r,0,0]
        #y = (4*r)/sqrt(3)
        #t2 = [0,-y,0]
        #fu.translate_coords([t1,t2,t3],[250,250,0])
        locs = {}
        terr1 = make_terrain((t1,t2,t3),locs,self.splits,self.smooths,self.pts_of_interest)
        locs = {}
        terr2 = make_terrain((t2,t4,t3),locs,self.splits,self.smooths,self.pts_of_interest)
        self.primitives = [terr1,terr2]
        #self.primitives[0].translate([0,0,-100])
        node.__init__(self, *args, **kwargs)
    





