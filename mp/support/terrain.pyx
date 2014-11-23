import mp_utils as mpu
cimport vector
from vector cimport vector
#import mp_vector as mpv
#from mpv import vector

from libc.math cimport sqrt

import time
import random as rm

stuff = 'hi'

cdef class terrain_point:

    cdef vector position
    cdef vector weights
    cdef list neighbors

    def __cinit__(self,x,y,z):
        self.position = vector(x,y,z)
        self._str = str((x,y))

    #    #self._default_('position',[0,0,0],**kwargs)
    #    #self._default_('neighbors',None,**kwargs)
    #    #self._default_('weights',[1,1,1],**kwargs)
    #    #self._str = str((self.position[0],self.position[1]))

    #cpdef set_position(self, pos):
    #    self.position = pos

    cpdef float relax(self, strength):
        centroid = vector.com([v.position for v in self.neighbors])
        svect = vector.vzip(self.weights,strength)
        move = vector.v1_v2(self.position,centroid).scale(svect)
        self.position.translate(move)
        return move.magnitude()

terrain_numbers = [0]
def get_terrain_number(repeat = False):
    if repeat: return str(terrain_numbers[0] - 1)
    num = terrain_numbers.pop(0)
    nex = num + 1
    terrain_numbers.append(nex)
    return str(num)

cdef class terrain_triangle:

    cdef list verts
    cdef list corners
    cdef list boundary_points
    cdef list children
    cdef list com_vects
    cdef vector center
    cdef int splits

    def __init__(self,list verts,list children,int splits):
        self.verts = verts
        self.children = children
        self.splits = splits

    cpdef set_verts(self, list verts):
        cdef list vposs = [v.position for v in verts]
        cdef vector center = vector.com(vposs)
        center = vector.com(vposs)
        center = vector.com(vposs)
        self.center = center
        self.verts = verts
        self.com_vects = [vector.v1_v2(v,center).normalize() for v in vposs]
        self.corners = [vector(v.x,v.y,v.z).translate(tv) 
                    for v,tv in zip(vposs,self.com_vects)]
    
    cdef float pick_zoff(self, float dist,int vcnt):
        cdef float rand = rm.random*2.0 - 1.0
        cdef float zoff = rand*(dist**(1.0/2.0))/float(vcnt)
        return zoff

    cdef terrain_point bisect(self,
            terrain_point tv1,terrain_point tv2,
            int vcnt,list controls,int control_count,
            int tolerance = 25,int big_tolerance = 250):

        cdef terrain_point newtv
        cdef vector newpos
        cdef float zoff
        cdef float zdiff
        cdef float dist

        if tv1 in tv2.neighbors and tv2 in tv1.neighbors:
            newpos = vector.midpoint(tv1.position,tv2.position)
            if control_count == 0:zoff = self.pick_zoff(1000**2,vcnt)
            else:
                ndex = vector.find_closest_xy(
                    newpos,controls,control_count,10.0)
                nearest = controls[ndex]
                dist = vector.distance_xy(nearest,newpos)
                zdiff = nearest.z - newpos.z

                if dist < tolerance: zoff = zdiff
                elif dist < big_tolerance: zoff = self.pick_zoff(dist,vcnt)
                else: zoff = self.pick_zoff(1000**2,vcnt)

            newpos.z += zoff

            newtv = terrain_point(newpos.x,newpos.y,newpos.z)
            newtv.neighbors = [tv1,tv2]
            tv1.neighbors.append(newtv)
            tv2.neighbors.append(newtv)
            tv1.neighbors.remove(tv2)
            tv2.neighbors.remove(tv1)

        else: newtv = [n for n in tv1.neighbors if n in tv2.neighbors][0]
        return newtv

    cpdef bisect_all(self, vcnt, controls, control_count):
        t1,t2,t3 = self.verts
        newt1 = self.bisect(t1,t2,vcnt,controls,control_count)
        newt2 = self.bisect(t2,t3,vcnt,controls,control_count)
        newt3 = self.bisect(t3,t1,vcnt,controls,control_count)
        newt1.neighbors.extend([newt2,newt3])
        newt2.neighbors.extend([newt3,newt1])
        newt3.neighbors.extend([newt1,newt2])
        return newt1,newt2,newt3

    cpdef fix_topology(self, locs = {}, lockeys = None):
        if lockeys is None: tempkeys = locs.keys()
        else: tempkeys = lockeys
        if not self.children:
            vcnt = len(self.verts)
            for vdx in range(vcnt):
            #for vdx,v in enumerate(self.verts):
                v = self.verts[vdx]
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
                locs, tempkeys = ch.fix_topology(
                    locs = locs, lockeys = tempkeys)
        return locs, tempkeys

    cpdef split(self, vcnt, controls, control_count, locs = None):
        if locs is None: locs = {}
        self.splits += 1
        if self.children:
            [ch.split(vcnt, controls, control_count, locs) for ch in self.children]
        else:
            t1,t2,t3 = self.verts
            newt1,newt2,newt3 = self.bisect_all(
                    vcnt, controls, control_count)
            self.children = [
                terrain_triangle(verts = [newt1,newt2,newt3]), 
                terrain_triangle(verts = [t1,newt1,newt3]), 
                terrain_triangle(verts = [t2,newt2,newt1]), 
                terrain_triangle(verts = [t3,newt3,newt2])]
            self.fix_topology(locs = locs)

    cpdef bint inside(self, vector pt):
        #corners = [mpu.translate_vector(v.position[:],tv) 
        #    for v,tv in zip(self.verts,self.com_vects)]
        return vector.inside(pt, self.corners)

    cpdef fix_closest(self, pts, locs):
        if not len(pts) == 0: return
        all_verts = locs.values()
        verts = [v.position for v in all_verts]
        vcnt = len(verts)
        for pt in pts:
            if not self.inside(pt): continue
            #nearest,neardis,neardex = mpu.find_closest_xy(pt,verts,vcnt)
            neardex = vector.find_closest_xy(pt,verts,vcnt,5.0)
            nearest = verts[neardex]
            #neardis = mpu.distance_xy(nearest,pt)
            closest = all_verts[neardex]
            q2 = pt.z - closest.position.z
            closest.position.z += q2
            newwt = all_verts[neardex].weights
            newwt.x = 0.0
            newwt.y = 0.0
            newwt.z = 0.0

    cpdef fix_bounds(self, object locs):
        cdef list all_verts = locs.values()
        cdef int bpts = 0
        cdef terrain_point uqvt

        self.boundary_points = []
        for uqvt in all_verts:
            if not self.inside(uqvt.position):
                uqvt.weights.x = 0.0
                uqvt.weights.y = 0.0
                #uqvt.weights.z = uqvt.weights.z
                #uqvt.weights = [0,0,uqvt.weights[2]]
                self.boundary_points.append(uqvt)
                bpts += 1
        print 'found',bpts,'boundary points in',len(all_verts),'points'

    cpdef smooth(self, int icnt, object locs):
        cdef list tpoints = locs.values()
        cdef float movement = 0.0
        cdef int idx
        for idx in range(icnt):
            for tp in tpoints:
                movement += tp.relax()
        return movement

    def meshes(self, lod = False):
        if lod:
            lod_meshes = []
            for ch in self.children:
                for subch in ch.children:
                    for subsubch in subch.children:
                        lod_meshes.append(subsubch.mesh(
                            depth = 0, max_depth = self.splits - 4))
            for lod in lod_meshes: lod.is_lod = True
            return lod_meshes
        else:
            meshes = []
            for ch in self.children:
                for subch in ch.children:
                    for subsubch in subch.children:
                        meshes.append(subsubch.mesh())
            for nonlod in meshes: nonlod.has_lod = True
            return meshes

    def mesh(self, depth = None, max_depth = None):
        verts = []
        nverts = []
        faces = []
        face_materials = []
        uvs = []
        #materials = ['ground']
        #materials = ['grass']
        materials = ['grass2']
        data = self.face_data(depth, max_depth)
        for fdx,fdat in enumerate(data):
            #newverts = [dcopy(f.position) for f in fdat]
            newverts = [f.position.to_list() for f in fdat]
            v1v2 = mpu.v1_v2(newverts[0],newverts[1])
            v1v3 = mpu.v1_v2(newverts[0],newverts[2])
            newnorml = [mpu.normalize(mpu.cross(v1v2,v1v3)) for f in fdat]
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
            'force_normal_calc' : True, 
                }
        new = arbitrary_primitive(**pwargs)
        new.phys_materials = ['/common/pmat/Grass']
        #new.phys_materials = ['/common/pmat/Stone']
        new.modified = True
        return new

    cdef int count_vertices(self):
        return 3**(self.splits+1)

    def face_data(self, depth = None, max_depth = None):
        data = []
        if not depth is None:
            if depth == max_depth:
                data.append(self.verts)
                return data
            else: depth += 1
        if self.children:
            [data.extend(ch.face_data(depth,max_depth)) 
                for ch in self.children]
        else: data.append(self.verts)
        return data

cpdef list filter(pts,tri):
    cdef list good = []
    for pt in pts:
        if pt in good: continue
        elif vector.inside(pt,tri): good.append(vector(*pt))
    return good

def make_terrain(initial_tps,splits = 2,smooths = 25,pts_of_interest = [[250,250,25],[500,250,-25]],locs = None):

    pts_of_interest = filter(pts_of_interest,initial_tps)
    poi_count = len(pts_of_interest)
    
    t1 = terrain_point(*initial_tps[0])
    t2 = terrain_point(*initial_tps[1])
    t3 = terrain_point(*initial_tps[2])
    t1.neighbors = [t2,t3]
    t2.neighbors = [t3,t1]
    t3.neighbors = [t1,t2]
    init_verts = [t1,t2,t3]
    terra = terrain_triangle(verts = init_verts)
    if locs is None: locs = {}
    for ivt in init_verts: locs[ivt._str] = ivt
    for sp in range(splits):
        vcnt = terra.count_vertices()
        terra.split(vcnt, pts_of_interest, poi_count, locs)
    terra.fix_bounds(locs)
    terra.fix_closest(pts_of_interest, locs)
    terra.smooth(smooths, locs)
    return terra, locs






